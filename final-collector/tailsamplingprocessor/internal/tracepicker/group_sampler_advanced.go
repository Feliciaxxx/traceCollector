package tracepicker

import (
	"fmt"
	"math/rand"

	"github.com/MaxHalford/eaopt"
)

// SampleVectorAdvanced 高级采样向量，实现完整的Python算法功能
type SampleVectorAdvanced struct {
	Genes   []int
	problem *SampleProblemAdvanced
}

// SampleProblemAdvanced 高级采样问题，对应Python的SampleProblem2
type SampleProblemAdvanced struct {
	// 基本参数
	RawDist   [][]float64      // (numTrace, numLabel)
	AbDist    [][]float64      // (numAbTrace, numLabel)
	Quotas    []int            // 每个代码的采样配额
	Bases     []int            // 每个代码的存储数量
	AllCombs  [][]*Combination // (combCount, numCode)
	CombCount int

	// 计算属性
	Splits   []int
	C        int // 总配额
	NumLabel int
	Dim      int

	// 百分位数和标准化
	Ps      []float64   // [0, 25, 50, 75, 90, 95, 99, 100]
	OriginP [][]float64 // (numLabel, 8)
	MaxV    []float64   // (numLabel)
	MinV    []float64   // (numLabel)

	// 遗传算法参数
	Lb []int // [0, 0, ..., 0]
	Ub []int // [combCount-1, combCount-1, ..., combCount-1]

	// 当前种群大小（用于计算）
	Np int
}

// NewSampleProblemAdvanced 创建高级采样问题
func NewSampleProblemAdvanced(rawDist, abDist [][]float64, quotas, bases []int, combCount int) (*SampleProblemAdvanced, error) {
	if combCount < 2 {
		return nil, fmt.Errorf("combCount must be larger than 2")
	}

	numLabel := len(rawDist[0])
	splits := make([]int, len(bases))
	sum := 0
	for i, base := range bases {
		sum += base
		splits[i] = sum
	}

	problem := &SampleProblemAdvanced{
		RawDist:   rawDist,
		AbDist:    abDist,
		Quotas:    quotas,
		Bases:     bases,
		CombCount: combCount,
		Splits:    splits,
		C:         sumInt(quotas),
		NumLabel:  numLabel,
		Dim:       len(quotas),
		Ps:        []float64{0, 25, 50, 75, 90, 95, 99, 100},
		Lb:        make([]int, len(quotas)),
		Ub:        make([]int, len(quotas)),
	}

	// 设置上下界
	for i := range problem.Ub {
		problem.Ub[i] = combCount - 1
	}

	// 初始化组合
	err := problem.initCombinations()
	if err != nil {
		return nil, err
	}

	// 计算原始数据的百分位数
	problem.calculateOriginPercentiles()

	return problem, nil
}

// initCombinations 初始化所有组合
func (sp *SampleProblemAdvanced) initCombinations() error {
	fmt.Printf("[DEBUG] Initializing combinations...\n")

	sp.AllCombs = make([][]*Combination, sp.CombCount)

	for combIdx := 0; combIdx < sp.CombCount; combIdx++ {
		sp.AllCombs[combIdx] = make([]*Combination, len(sp.Quotas))

		start := 0
		for codeIdx, quota := range sp.Quotas {
			end := sp.Splits[codeIdx]

			// 随机采样生成组合
			if end-start < quota {
				return fmt.Errorf("not enough data for code %d: need %d, have %d", codeIdx, quota, end-start)
			}

			comb := randomSampleRange(start, end, quota)
			sp.AllCombs[combIdx][codeIdx] = NewCombination(comb)

			start = end
		}
	}

	fmt.Printf("[DEBUG] Initialized %d combinations for %d codes\n", sp.CombCount, len(sp.Quotas))
	return nil
}

// calculateOriginPercentiles 计算原始数据的百分位数
func (sp *SampleProblemAdvanced) calculateOriginPercentiles() {
	// 合并原始数据和异常数据
	var allData [][]float64
	if len(sp.AbDist) > 0 {
		allData = make([][]float64, len(sp.RawDist)+len(sp.AbDist))
		copy(allData, sp.RawDist)
		copy(allData[len(sp.RawDist):], sp.AbDist)
	} else {
		allData = sp.RawDist
	}

	// 转置数据：(numTrace, numLabel) -> (numLabel, numTrace)
	transposed := transposeMatrix(allData)

	sp.OriginP = make([][]float64, sp.NumLabel)
	sp.MaxV = make([]float64, sp.NumLabel)
	sp.MinV = make([]float64, sp.NumLabel)

	for labelIdx, labelData := range transposed {
		// 计算百分位数
		sp.OriginP[labelIdx] = make([]float64, len(sp.Ps))
		for i, p := range sp.Ps {
			sp.OriginP[labelIdx][i] = calculatePercentile(labelData, p)
		}

		// 计算最大值和最小值
		sp.MaxV[labelIdx] = maxFloat64(labelData)
		sp.MinV[labelIdx] = minFloat64(labelData)

		// 标准化原始百分位数
		for i := range sp.OriginP[labelIdx] {
			sp.OriginP[labelIdx][i] = (sp.OriginP[labelIdx][i] - sp.MinV[labelIdx]) / (sp.MaxV[labelIdx] - sp.MinV[labelIdx] + 1e-7)
		}
	}

	fmt.Printf("[DEBUG] Calculated percentiles for %d labels\n", sp.NumLabel)
}

// GetIdxsByVar 根据基因获取采样索引
func (sp *SampleProblemAdvanced) GetIdxsByVar(genes []int) []int {
	var result []int

	for codeIdx, gene := range genes {
		if gene >= 0 && gene < len(sp.AllCombs) && codeIdx < len(sp.AllCombs[gene]) {
			comb := sp.AllCombs[gene][codeIdx]
			result = append(result, comb.Comb...)
		}
	}

	return result
}

// Consistency 计算一致性（对应Python的consistency方法）
func (sp *SampleProblemAdvanced) Consistency(matrix [][]float64) []float64 {
	// matrix: (Np * numLabel, C)
	var sample [][]float64

	if len(sp.AbDist) > 0 {
		// 转置 AbDist: (numAbTrace, numLabel) -> (numLabel, numAbTrace)
		abDistT := transposeMatrix(sp.AbDist)

		// 复制 abDistT Np 次
		tileAbDist := make([][]float64, sp.Np*sp.NumLabel)
		for i := 0; i < sp.Np; i++ {
			for j := 0; j < sp.NumLabel; j++ {
				tileAbDist[i*sp.NumLabel+j] = make([]float64, len(abDistT[j]))
				copy(tileAbDist[i*sp.NumLabel+j], abDistT[j])
			}
		}

		// 水平拼接 matrix 和 tileAbDist
		sample = make([][]float64, len(matrix))
		for i := 0; i < len(matrix); i++ {
			sample[i] = append(matrix[i], tileAbDist[i]...)
		}
	} else {
		sample = matrix
	}

	// 计算采样数据的百分位数
	sampleP := make([][]float64, len(sample))
	for i := 0; i < len(sample); i++ {
		sampleP[i] = make([]float64, len(sp.Ps))
		for j, p := range sp.Ps {
			sampleP[i][j] = calculatePercentile(sample[i], p)
		}
	}

	// 复制原始百分位数 Np 次
	originP := make([][]float64, sp.Np*sp.NumLabel)
	for i := 0; i < sp.Np; i++ {
		for j := 0; j < sp.NumLabel; j++ {
			originP[i*sp.NumLabel+j] = make([]float64, len(sp.OriginP[j]))
			copy(originP[i*sp.NumLabel+j], sp.OriginP[j])
		}
	}

	// 标准化采样百分位数
	for i := 0; i < len(sampleP); i++ {
		labelIdx := i % sp.NumLabel
		for j := 0; j < len(sampleP[i]); j++ {
			sampleP[i][j] = (sampleP[i][j] - sp.MinV[labelIdx]) / (sp.MaxV[labelIdx] - sp.MinV[labelIdx] + 1e-7)
		}
	}

	// 计算RMSE
	result := make([]float64, sp.Np)
	for i := 0; i < sp.Np; i++ {
		var mseSum float64
		for j := 0; j < sp.NumLabel; j++ {
			idx := i*sp.NumLabel + j
			var mse float64
			for k := 0; k < len(sp.Ps); k++ {
				diff := sampleP[idx][k] - originP[idx][k]
				mse += diff * diff
			}
			mse /= float64(len(sp.Ps))
			mseSum += mse
		}
		result[i] = mseSum
	}

	return result
}

// EvalVars 评估变量（对应Python的evalVars方法）
func (sp *SampleProblemAdvanced) EvalVars(vars [][]int) []float64 {
	sp.Np = len(vars)

	// 获取采样数据
	sampleData := make([][][]float64, sp.Np)
	for i, varSet := range vars {
		indices := sp.GetIdxsByVar(varSet)
		sampleData[i] = make([][]float64, len(indices))
		for j, idx := range indices {
			if idx < len(sp.RawDist) {
				sampleData[i][j] = make([]float64, len(sp.RawDist[idx]))
				copy(sampleData[i][j], sp.RawDist[idx])
			}
		}
	}

	// 转换数据格式：(Np, C, numLabel) -> (Np, numLabel, C) -> (Np * numLabel, C)
	matrix := make([][]float64, sp.Np*sp.NumLabel)
	for i := 0; i < sp.Np; i++ {
		for j := 0; j < sp.NumLabel; j++ {
			matrix[i*sp.NumLabel+j] = make([]float64, sp.C)
			for k := 0; k < sp.C && k < len(sampleData[i]); k++ {
				if j < len(sampleData[i][k]) {
					matrix[i*sp.NumLabel+j][k] = sampleData[i][k][j]
				}
			}
		}
	}

	return sp.Consistency(matrix)
}

// Evaluate 实现完整的适应度评估
func (sv *SampleVectorAdvanced) Evaluate() (float64, error) {
	if sv.problem == nil {
		return 1000.0, fmt.Errorf("problem not initialized")
	}

	vars := [][]int{sv.Genes}
	fitness := sv.problem.EvalVars(vars)
	if len(fitness) == 0 {
		return 1000.0, fmt.Errorf("evaluation failed")
	}

	return fitness[0], nil
}

// Mutate 变异操作
func (sv *SampleVectorAdvanced) Mutate(rng *rand.Rand) {
	if sv.problem == nil || len(sv.Genes) == 0 {
		return
	}

	// 随机选择一个基因进行变异
	idx := rng.Intn(len(sv.Genes))
	if idx < len(sv.problem.Ub) {
		sv.Genes[idx] = rng.Intn(sv.problem.Ub[idx]-sv.problem.Lb[idx]+1) + sv.problem.Lb[idx]
	}
}

// Crossover 交叉操作
func (sv *SampleVectorAdvanced) Crossover(other eaopt.Genome, rng *rand.Rand) {
	otherSV, ok := other.(*SampleVectorAdvanced)
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

// Clone 克隆操作
func (sv *SampleVectorAdvanced) Clone() eaopt.Genome {
	clonedGenes := make([]int, len(sv.Genes))
	copy(clonedGenes, sv.Genes)

	return &SampleVectorAdvanced{
		Genes:   clonedGenes,
		problem: sv.problem,
	}
}

// NewSampleVectorAdvanced 创建高级采样向量
func NewSampleVectorAdvanced(problem *SampleProblemAdvanced) *SampleVectorAdvanced {
	if problem == nil || problem.Dim <= 0 {
		return &SampleVectorAdvanced{
			Genes:   []int{0},
			problem: problem,
		}
	}

	genes := make([]int, problem.Dim)
	for i := 0; i < problem.Dim; i++ {
		if i < len(problem.Ub) {
			genes[i] = rand.Intn(problem.Ub[i]-problem.Lb[i]+1) + problem.Lb[i]
		}
	}

	return &SampleVectorAdvanced{
		Genes:   genes,
		problem: problem,
	}
}

// 辅助函数

func sumInt(slice []int) int {
	sum := 0
	for _, v := range slice {
		sum += v
	}
	return sum
}

func maxFloat64(data []float64) float64 {
	if len(data) == 0 {
		return 0
	}

	maxVal := data[0]
	for _, v := range data[1:] {
		if v > maxVal {
			maxVal = v
		}
	}
	return maxVal
}

func minFloat64(data []float64) float64 {
	if len(data) == 0 {
		return 0
	}

	minVal := data[0]
	for _, v := range data[1:] {
		if v < minVal {
			minVal = v
		}
	}
	return minVal
}

func transposeMatrix(matrix [][]float64) [][]float64 {
	if len(matrix) == 0 {
		return nil
	}

	rows := len(matrix)
	cols := len(matrix[0])
	result := make([][]float64, cols)

	for i := 0; i < cols; i++ {
		result[i] = make([]float64, rows)
		for j := 0; j < rows; j++ {
			result[i][j] = matrix[j][i]
		}
	}

	return result
}

func calculatePercentile(data []float64, p float64) float64 {
	if len(data) == 0 {
		return 0
	}

	// 手动排序
	sorted := make([]float64, len(data))
	copy(sorted, data)

	// 简单冒泡排序
	for i := 0; i < len(sorted); i++ {
		for j := 0; j < len(sorted)-1-i; j++ {
			if sorted[j] > sorted[j+1] {
				sorted[j], sorted[j+1] = sorted[j+1], sorted[j]
			}
		}
	}

	if p <= 0 {
		return sorted[0]
	}
	if p >= 100 {
		return sorted[len(sorted)-1]
	}

	index := p / 100.0 * float64(len(sorted)-1)
	lower := int(index)
	upper := lower + 1

	if upper >= len(sorted) {
		return sorted[lower]
	}

	if lower == upper {
		return sorted[lower]
	}

	weight := index - float64(lower)
	return sorted[lower]*(1-weight) + sorted[upper]*weight
}

func randomSampleRange(start, end, n int) []int {
	if n > end-start {
		panic("sample size larger than population")
	}

	population := make([]int, end-start)
	for i := 0; i < end-start; i++ {
		population[i] = start + i
	}

	// Fisher-Yates shuffle的前n个元素
	for i := 0; i < n; i++ {
		j := i + rand.Intn(len(population)-i)
		population[i], population[j] = population[j], population[i]
	}

	return population[:n]
}
