// metadata.go - 简化的元数据定义

package tailsamplingprocessor

import (
	"go.opentelemetry.io/collector/component"
)

var (
	Type            = component.MustNewType("tail_sampling")
	TracesStability = component.StabilityLevelBeta
)
