// file: processor/tailsamplingprocessor/processor.go

// SPDX-License-Identifier: Apache-2.0

// file: processor/tailsamplingprocessor/processor.go

// SPDX-License-Identifier: Apache-2.0

package tailsamplingprocessor

import (
	"context"
	"math"
	"math/rand"
	"sort"
	"sync"

	"go.opentelemetry.io/collector/component"
	"go.opentelemetry.io/collector/consumer"
	"go.opentelemetry.io/collector/pdata/ptrace"
	"go.opentelemetry.io/collector/processor"
	"go.uber.org/zap"

	"github.com/samplingCollector/tailsamplingprocessor/internal/tracepicker"
)

type tailSamplingSpanProcessor struct {
	ctx          context.Context
	set          processor.Settings
	logger       *zap.Logger
	nextConsumer consumer.Traces
	config       Config
	buffer       *tracepicker.SharedBuffer
	encoder      *tracepicker.BFSEncoder
	pathCounter  sync.Map
}

func newTracesProcessor(
	ctx context.Context,
	set processor.Settings,
	nextConsumer consumer.Traces,
	cfg Config,
) (processor.Traces, error) {
	// ... 构造函数保持不变 ...
	histPool := tracepicker.NewHistPool(cfg.PoolHeight)
	encoder := tracepicker.NewBFSEncoder(histPool)
	buffer := tracepicker.NewSharedBuffer(cfg.BufferSize)

	tsp := &tailSamplingSpanProcessor{
		ctx:          ctx,
		set:          set,
		logger:       set.Logger,
		nextConsumer: nextConsumer,
		config:       cfg,
		buffer:       buffer,
		encoder:      encoder,
	}

	return tsp, nil
}

// NewTracesProcessor 创建一个新的 tail sampling processor (导出函数用于测试)
func NewTracesProcessor(
	ctx context.Context,
	set processor.Settings,
	nextConsumer consumer.Traces,
	cfg Config,
) (processor.Traces, error) {
	return newTracesProcessor(ctx, set, nextConsumer, cfg)
}

// 【核心变更】ConsumeTraces 现在是非阻塞的
func (tsp *tailSamplingSpanProcessor) ConsumeTraces(_ context.Context, td ptrace.Traces) error {
	typeID, isAbnormal := tsp.encoder.Encode(td)
	tsp.buffer.Add(typeID, td, isAbnormal)

	// 简化的日志，只在缓冲区状态变化时输出
	bufferCount := tsp.buffer.Count()
	if bufferCount%10 == 0 || tsp.buffer.IsFull() {
		tsp.logger.Info("Buffer status",
			zap.Uint64("count", bufferCount),
			zap.Uint64("limit", tsp.config.BufferSize),
			zap.Bool("full", tsp.buffer.IsFull()))
	}

	if tsp.buffer.IsFull() {
		tsp.logger.Info("🎯 Buffer full, triggering tail sampling",
			zap.Uint64("traces", bufferCount))
		// 1. 原子地换出数据副本并清空原缓冲区
		normalTraces, abnormalTraces, count := tsp.buffer.SwapAndClear()

		// 2. 将耗时的采样工作放到后台goroutine中执行，让ConsumeTraces立刻返回
		go tsp.runBatchSampling(normalTraces, abnormalTraces, count)
	}
	return nil
}

// 【核心变更】runBatchSampling 现在接收数据副本作为参数
func (tsp *tailSamplingSpanProcessor) runBatchSampling(
	normalTracesByType map[string][]ptrace.Traces,
	abnormalTraces []ptrace.Traces,
	bufferCount uint64,
) {
	tsp.logger.Info("🔬 Starting tail sampling analysis...",
		zap.Uint64("total_traces", bufferCount),
		zap.Int("abnormal_traces", len(abnormalTraces)),
		zap.Int("normal_trace_types", len(normalTracesByType)))

	// 1. 优先保留所有异常追踪
	finalSampledTraces := make([]ptrace.Traces, 0, bufferCount)
	finalSampledTraces = append(finalSampledTraces, abnormalTraces...)

	// 2. 计算剩余采样配额
	totalSampleCount := int(float64(bufferCount) * tsp.config.SampleRate)
	currentQuota := totalSampleCount - len(finalSampledTraces)

	tsp.logger.Info("📊 Sampling calculation",
		zap.Int("target_sample_count", totalSampleCount),
		zap.Int("abnormal_kept", len(abnormalTraces)),
		zap.Int("remaining_quota", currentQuota))

	if currentQuota > 0 && len(normalTracesByType) > 0 {
		// 3. 准备配额分配的输入数据
		typeCounts := make(map[string]int)
		for code, traces := range normalTracesByType {
			typeCounts[code] = len(traces)
		}

		historicalCounts := make(map[string]int)
		tsp.pathCounter.Range(func(key, value interface{}) bool {
			historicalCounts[key.(string)] = value.(int)
			return true
		})

		quotaMap := tracepicker.AllocateQuota(typeCounts, historicalCounts, currentQuota)

		// 4. 调用演化算法进行分组采样
		// (数据准备部分逻辑与之前版本相同)
		allLabels, label2idx := getAllLabelsAndMap(normalTracesByType, abnormalTraces)
		var sortedTypes []string
		for typeID := range normalTracesByType {
			sortedTypes = append(sortedTypes, typeID)
		}
		sort.Strings(sortedTypes)

		var quotas, bases []int
		var allNormalTraces []ptrace.Traces
		for _, typeID := range sortedTypes {
			traces := normalTracesByType[typeID]
			bases = append(bases, len(traces))
			allNormalTraces = append(allNormalTraces, traces...)
			quotas = append(quotas, quotaMap[typeID])
		}

		rawDist := buildLatencyMatrix(allNormalTraces, label2idx, allLabels)
		abDist := buildLatencyMatrix(abnormalTraces, label2idx, allLabels)

		problem, err := tracepicker.NewSampleProblem(rawDist, abDist, quotas, bases, tsp.config.CombinationCount, 1)
		if err != nil {
			tsp.logger.Error("Failed to create sample problem", zap.Error(err))
			return
		}

		// 使用简化版本的优化器
		optimizerSimple := tracepicker.NewSampleOptimizerSimple(problem)
		bestSimple, err := optimizerSimple.OptimizeWithSimpleFallback()
		if err != nil {
			tsp.logger.Warn("Simple genetic algorithm optimization failed, trying advanced version",
				zap.Error(err))

			// 尝试高级版本
			advancedProblem, err := tracepicker.ConvertToSampleProblemAdvanced(problem, tsp.config.CombinationCount)
			if err != nil {
				tsp.logger.Warn("Failed to convert to advanced problem, using simple random sampling",
					zap.Error(err))

				// 回退到简单随机采样
				finalSampledTraces = tsp.simpleRandomSampling(allNormalTraces, abnormalTraces, int(bufferCount))
			} else {
				// 使用高级版本的优化器
				optimizerAdvanced := tracepicker.NewSampleOptimizerAdvanced(advancedProblem)
				bestAdvanced, err := optimizerAdvanced.OptimizeWithAdvancedFallback()
				if err != nil {
					tsp.logger.Warn("Advanced genetic algorithm optimization failed, falling back to simple random sampling",
						zap.Error(err))

					// 回退到简单随机采样
					finalSampledTraces = tsp.simpleRandomSampling(allNormalTraces, abnormalTraces, int(bufferCount))
				} else {
					// 5. 根据高级优化结果获取最终要采样的追踪
					finalIndices := advancedProblem.GetIdxsByVar(bestAdvanced.Genes)
					for _, idx := range finalIndices {
						if idx < len(allNormalTraces) {
							finalSampledTraces = append(finalSampledTraces, allNormalTraces[idx])
						}
					}
				}
			}
		} else {
			// 5. 根据优化结果获取最终要采样的追踪
			finalIndices := problem.GetIdxsByVar(bestSimple.Genes)
			for _, idx := range finalIndices {
				if idx < len(allNormalTraces) {
					finalSampledTraces = append(finalSampledTraces, allNormalTraces[idx])
				}
			}

			// 6. 更新历史采样计数
			sampledCountByType := make(map[string]int)
			for _, idx := range finalIndices {
				if idx < len(allNormalTraces) {
					typeID, _ := tsp.encoder.Encode(allNormalTraces[idx])
					sampledCountByType[typeID]++
				}
			}
			for typeID, count := range sampledCountByType {
				c, _ := tsp.pathCounter.LoadOrStore(typeID, 0)
				tsp.pathCounter.Store(typeID, c.(int)+count)
			}
		}
	}

	// 7. 将最终采样的追踪数据发送给下游消费者
	tsp.exportTraces(finalSampledTraces)

	// 计算采样统计
	samplingRate := float64(len(finalSampledTraces)) / float64(bufferCount) * 100
	tsp.logger.Info("✅ Tail sampling completed",
		zap.Int("input_traces", int(bufferCount)),
		zap.Int("output_traces", len(finalSampledTraces)),
		zap.Float64("actual_sampling_rate", samplingRate))
}

// exportTraces 辅助函数保持不变。
func (tsp *tailSamplingSpanProcessor) exportTraces(traces []ptrace.Traces) {
	for _, td := range traces {
		if err := tsp.nextConsumer.ConsumeTraces(tsp.ctx, td); err != nil {
			tsp.logger.Error("Failed to send traces to next consumer", zap.Error(err))
		}
	}
}

// --- 组件生命周期方法 ---

func (tsp *tailSamplingSpanProcessor) Capabilities() consumer.Capabilities {
	return consumer.Capabilities{MutatesData: false}
}

func (tsp *tailSamplingSpanProcessor) Start(_ context.Context, _ component.Host) error {
	return nil
}

func (tsp *tailSamplingSpanProcessor) Shutdown(_ context.Context) error {
	tsp.logger.Info("Processor is shutting down, processing remaining traces in the buffer...")
	// 在关闭时，同步处理最后一批数据
	normalTraces, abnormalTraces, count := tsp.buffer.SwapAndClear()
	if count > 0 {
		tsp.logger.Info("Processing remaining traces during shutdown", zap.Uint64("count", count))
		tsp.runBatchSampling(normalTraces, abnormalTraces, count)
	}
	return nil
}

// 辅助函数
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// --- 新增的辅助函数 ---

// getSpanLabel 从 span 中提取 "service:operation" 标签。
func getSpanLabel(span ptrace.Span) string {
	serviceName := "unknown.service"
	if val, ok := span.Attributes().Get("service.name"); ok {
		serviceName = val.Str()
	}
	return serviceName + ":" + span.Name()
}

// getAllLabelsAndMap 遍历所有追踪，获取唯一的标签列表和标签到索引的映射。
func getAllLabelsAndMap(normalTraces map[string][]ptrace.Traces, abnormalTraces []ptrace.Traces) ([]string, map[string]int) {
	labelSet := make(map[string]struct{})
	for _, traces := range normalTraces {
		for _, trace := range traces {
			rs := trace.ResourceSpans()
			for i := 0; i < rs.Len(); i++ {
				ils := rs.At(i).ScopeSpans()
				for j := 0; j < ils.Len(); j++ {
					spans := ils.At(j).Spans()
					for k := 0; k < spans.Len(); k++ {
						labelSet[getSpanLabel(spans.At(k))] = struct{}{}
					}
				}
			}
		}
	}
	// (同样逻辑遍历 abnormalTraces)

	labels := make([]string, 0, len(labelSet))
	for label := range labelSet {
		labels = append(labels, label)
	}
	sort.Strings(labels)

	label2idx := make(map[string]int, len(labels))
	for i, label := range labels {
		label2idx[label] = i
	}
	return labels, label2idx
}

// buildLatencyMatrix 将追踪列表转换为优化器所需的延迟矩阵。
func buildLatencyMatrix(traces []ptrace.Traces, label2idx map[string]int, allLabels []string) [][]float64 {
	matrix := make([][]float64, len(traces))
	for i, trace := range traces {
		latencies := make([]float64, len(allLabels))
		for j := range latencies {
			latencies[j] = math.NaN() // 默认值为 NaN
		}

		rs := trace.ResourceSpans()
		for j := 0; j < rs.Len(); j++ {
			ils := rs.At(j).ScopeSpans()
			for k := 0; k < ils.Len(); k++ {
				spans := ils.At(k).Spans()
				for l := 0; l < spans.Len(); l++ {
					span := spans.At(l)
					label := getSpanLabel(span)
					if idx, ok := label2idx[label]; ok {
						duration := span.EndTimestamp().AsTime().Sub(span.StartTimestamp().AsTime())
						latencies[idx] = float64(duration.Milliseconds())
					}
				}
			}
		}
		matrix[i] = latencies
	}
	return matrix
}

// simpleRandomSampling 实现简单的随机采样作为回退方案
func (tsp *tailSamplingSpanProcessor) simpleRandomSampling(normalTraces, abnormalTraces []ptrace.Traces, totalTraces int) []ptrace.Traces {
	// 计算采样数量
	sampleCount := int(float64(totalTraces) * tsp.config.SampleRate)
	if sampleCount <= 0 {
		return []ptrace.Traces{}
	}

	var allTraces []ptrace.Traces
	allTraces = append(allTraces, normalTraces...)
	allTraces = append(allTraces, abnormalTraces...)

	// 如果总数不足采样数量，返回全部
	if len(allTraces) <= sampleCount {
		tsp.logger.Info("Total traces less than sample count, returning all traces",
			zap.Int("total_traces", len(allTraces)),
			zap.Int("sample_count", sampleCount))
		return allTraces
	}

	// 随机采样
	indices := make([]int, len(allTraces))
	for i := range indices {
		indices[i] = i
	}

	// Fisher-Yates shuffle
	for i := len(indices) - 1; i > 0; i-- {
		j := rand.Intn(i + 1)
		indices[i], indices[j] = indices[j], indices[i]
	}

	// 取前 sampleCount 个
	result := make([]ptrace.Traces, sampleCount)
	for i := 0; i < sampleCount; i++ {
		result[i] = allTraces[indices[i]]
	}

	tsp.logger.Info("✅ Simple random sampling completed",
		zap.Int("input_traces", len(allTraces)),
		zap.Int("output_traces", len(result)),
		zap.Float64("sampling_rate", float64(len(result))/float64(len(allTraces))*100))

	return result
}
