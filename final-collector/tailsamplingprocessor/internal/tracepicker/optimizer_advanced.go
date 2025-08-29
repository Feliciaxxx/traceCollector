package tracepicker

import (
	"fmt"
	"math/rand"

	"github.com/MaxHalford/eaopt"
)

// SampleOptimizerAdvanced 高级采样优化器
type SampleOptimizerAdvanced struct {
	Problem *SampleProblemAdvanced
}

// NewSampleOptimizerAdvanced 创建高级优化器
func NewSampleOptimizerAdvanced(problem *SampleProblemAdvanced) *SampleOptimizerAdvanced {
	return &SampleOptimizerAdvanced{
		Problem: problem,
	}
}

// OptimizeAdvanced 执行高级遗传算法优化
func (so *SampleOptimizerAdvanced) OptimizeAdvanced() (*SampleVectorAdvanced, error) {
	if so.Problem == nil {
		return nil, fmt.Errorf("problem not set")
	}

	fmt.Printf("[DEBUG] Starting advanced genetic algorithm optimization...\n")

	// 创建工厂函数
	factory := func(rng *rand.Rand) eaopt.Genome {
		return NewSampleVectorAdvanced(so.Problem)
	}

	// 配置遗传算法
	config := eaopt.NewDefaultGAConfig()
	config.NPops = 1
	config.PopSize = 20      // 增加种群大小以获得更好的解
	config.NGenerations = 10 // 增加代数

	fmt.Printf("[DEBUG] Creating advanced GA with config: NPops=%d, PopSize=%d, NGenerations=%d\n",
		config.NPops, config.PopSize, config.NGenerations)

	// 创建遗传算法实例
	ga, err := config.NewGA()
	if err != nil {
		return nil, fmt.Errorf("failed to create GA: %v", err)
	}

	fmt.Printf("[DEBUG] Running advanced GA minimize...\n")
	// 运行最小化
	err = ga.Minimize(factory)
	if err != nil {
		return nil, fmt.Errorf("GA minimize failed: %v", err)
	}

	fmt.Printf("[DEBUG] Getting best individual from HallOfFame...\n")

	// 获取最佳个体
	if len(ga.HallOfFame) == 0 {
		return nil, fmt.Errorf("no individuals in hall of fame")
	}

	bestIndividual := ga.HallOfFame[0]
	fmt.Printf("[DEBUG] Best individual type: %T, fitness: %f\n",
		bestIndividual.Genome, bestIndividual.Fitness)

	// 类型断言
	bestGenome, ok := bestIndividual.Genome.(*SampleVectorAdvanced)
	if !ok {
		return nil, fmt.Errorf("unexpected genome type: %T", bestIndividual.Genome)
	}

	fmt.Printf("[DEBUG] Successfully optimized with %d genes, fitness: %f\n",
		len(bestGenome.Genes), bestIndividual.Fitness)
	return bestGenome, nil
}

// OptimizeWithAdvancedFallback 带回退的高级优化
func (so *SampleOptimizerAdvanced) OptimizeWithAdvancedFallback() (*SampleVectorAdvanced, error) {
	// 创建回退解决方案
	fallback := NewSampleVectorAdvanced(so.Problem)

	// 尝试遗传算法优化
	result, err := so.OptimizeAdvanced()
	if err != nil {
		fmt.Printf("[WARN] Advanced genetic algorithm failed: %v, using fallback\n", err)
		return fallback, nil
	}

	return result, nil
}

// ConvertToSampleProblemAdvanced 将原始SampleProblem转换为高级版本
func ConvertToSampleProblemAdvanced(oldProblem *SampleProblem, combCount int) (*SampleProblemAdvanced, error) {
	if oldProblem == nil {
		return nil, fmt.Errorf("old problem is nil")
	}

	if combCount <= 0 {
		combCount = 10 // 默认组合数量
	}

	// 创建高级问题
	advancedProblem, err := NewSampleProblemAdvanced(
		oldProblem.RawDist,
		oldProblem.AbDist,
		oldProblem.Quotas,
		oldProblem.Bases,
		combCount,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create advanced problem: %v", err)
	}

	fmt.Printf("[DEBUG] Converted problem: %d labels, %d codes, %d combinations\n",
		advancedProblem.NumLabel, len(advancedProblem.Quotas), combCount)

	return advancedProblem, nil
}
