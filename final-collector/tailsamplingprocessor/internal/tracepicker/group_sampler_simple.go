package tracepicker

import (
	"fmt"
	"math/rand"

	"github.com/MaxHalford/eaopt"
)

// SampleVectorSimple 简化的采样向量，确保类型安全
type SampleVectorSimple struct {
	Genes   []int
	problem *SampleProblem
}

// Evaluate 计算适应度值 - 必须是指针接收者
func (sv *SampleVectorSimple) Evaluate() (float64, error) {
	if sv.problem == nil {
		return -1000.0, fmt.Errorf("problem not set")
	}

	if len(sv.Genes) == 0 {
		return -999.0, nil
	}

	// 计算基本适应度
	var fitness float64
	for _, gene := range sv.Genes {
		fitness += float64(gene)
	}

	// 添加约束惩罚
	penalty := 0.0
	for i, gene := range sv.Genes {
		if i < len(sv.problem.Lb) && gene < sv.problem.Lb[i] {
			penalty += 10.0
		}
		if i < len(sv.problem.Ub) && gene > sv.problem.Ub[i] {
			penalty += 10.0
		}
	}

	return fitness - penalty, nil
}

// Mutate 变异操作 - 必须是指针接收者
func (sv *SampleVectorSimple) Mutate(rng *rand.Rand) {
	if len(sv.Genes) == 0 || sv.problem == nil {
		return
	}

	// 随机选择一个基因进行变异
	idx := rng.Intn(len(sv.Genes))

	if idx < len(sv.problem.Lb) && idx < len(sv.problem.Ub) {
		// 在范围内随机变异
		sv.Genes[idx] = sv.problem.Lb[idx] + rng.Intn(sv.problem.Ub[idx]-sv.problem.Lb[idx]+1)
	}
}

// Crossover 交叉操作 - 必须是指针接收者
func (sv *SampleVectorSimple) Crossover(other eaopt.Genome, rng *rand.Rand) {
	otherSV, ok := other.(*SampleVectorSimple)
	if !ok || len(sv.Genes) != len(otherSV.Genes) {
		return
	}

	// 单点交叉
	if len(sv.Genes) > 1 {
		crossPoint := rng.Intn(len(sv.Genes))
		for i := crossPoint; i < len(sv.Genes); i++ {
			sv.Genes[i], otherSV.Genes[i] = otherSV.Genes[i], sv.Genes[i]
		}
	}
}

// Clone 克隆操作 - 必须是指针接收者
func (sv *SampleVectorSimple) Clone() eaopt.Genome {
	clonedGenes := make([]int, len(sv.Genes))
	copy(clonedGenes, sv.Genes)

	return &SampleVectorSimple{
		Genes:   clonedGenes,
		problem: sv.problem,
	}
}

// NewSampleVectorSimple 创建新的采样向量
func NewSampleVectorSimple(problem *SampleProblem) *SampleVectorSimple {
	if problem == nil || problem.Dim <= 0 {
		return &SampleVectorSimple{
			Genes:   []int{1}, // 默认值
			problem: problem,
		}
	}

	genes := make([]int, problem.Dim)
	for i := 0; i < problem.Dim; i++ {
		if i < len(problem.Lb) && i < len(problem.Ub) {
			// 随机初始化在范围内
			if problem.Ub[i] > problem.Lb[i] {
				genes[i] = problem.Lb[i] + rand.Intn(problem.Ub[i]-problem.Lb[i]+1)
			} else {
				genes[i] = problem.Lb[i]
			}
		}
	}

	return &SampleVectorSimple{
		Genes:   genes,
		problem: problem,
	}
}

// SampleOptimizerSimple 简化的采样优化器
type SampleOptimizerSimple struct {
	Problem *SampleProblem
}

// NewSampleOptimizerSimple 创建简化的优化器
func NewSampleOptimizerSimple(problem *SampleProblem) *SampleOptimizerSimple {
	return &SampleOptimizerSimple{
		Problem: problem,
	}
}

// OptimizeSimple 执行简化的优化
func (so *SampleOptimizerSimple) OptimizeSimple() (*SampleVectorSimple, error) {
	if so.Problem == nil {
		return nil, fmt.Errorf("problem not set")
	}

	fmt.Printf("[DEBUG] Starting simple genetic algorithm optimization...\n")

	// 创建工厂函数
	factory := func(rng *rand.Rand) eaopt.Genome {
		return NewSampleVectorSimple(so.Problem)
	}

	// 配置遗传算法
	config := eaopt.NewDefaultGAConfig()
	config.NPops = 1
	config.PopSize = 10     // 减少种群大小
	config.NGenerations = 5 // 减少代数

	fmt.Printf("[DEBUG] Creating GA with config: NPops=%d, PopSize=%d, NGenerations=%d\n",
		config.NPops, config.PopSize, config.NGenerations)

	// 创建遗传算法实例
	ga, err := config.NewGA()
	if err != nil {
		return nil, fmt.Errorf("failed to create GA: %v", err)
	}

	fmt.Printf("[DEBUG] Running GA minimize...\n")
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
	fmt.Printf("[DEBUG] Best individual type: %T\n", bestIndividual.Genome)

	// 类型断言
	bestGenome, ok := bestIndividual.Genome.(*SampleVectorSimple)
	if !ok {
		return nil, fmt.Errorf("unexpected genome type: %T", bestIndividual.Genome)
	}

	fmt.Printf("[DEBUG] Successfully optimized with %d genes\n", len(bestGenome.Genes))
	return bestGenome, nil
}

// OptimizeWithSimpleFallback 带回退的优化
func (so *SampleOptimizerSimple) OptimizeWithSimpleFallback() (*SampleVectorSimple, error) {
	// 创建回退解决方案
	fallback := NewSampleVectorSimple(so.Problem)

	// 尝试遗传算法优化
	result, err := so.OptimizeSimple()
	if err != nil {
		fmt.Printf("[WARN] Genetic algorithm failed: %v, using fallback\n", err)
		return fallback, nil
	}

	return result, nil
}
