// metadata.go - 简化的元数据定义

package groupbytraceprocessor

import (
	"go.opentelemetry.io/collector/component"
)

var (
	Type            = component.MustNewType("groupbytrace")
	TracesStability = component.StabilityLevelBeta
)
