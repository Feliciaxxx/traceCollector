// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package tailsamplingprocessor

import (
	"context"
	"time"

	"go.opentelemetry.io/collector/component"
	"go.opentelemetry.io/collector/consumer"
	"go.opentelemetry.io/collector/processor"
)

// NewFactory returns a new factory for the Tail Sampling processor.
func NewFactory() processor.Factory {
	return processor.NewFactory(
		Type,
		createDefaultConfig,
		processor.WithTraces(createTracesProcessor, TracesStability))
}

func createDefaultConfig() component.Config {
	return &Config{
		SampleRate:       0.1,  // 默认采样率 10%
		BufferSize:       4000, // 默认缓冲区大小 4000
		PoolHeight:       1000, // 默认历史池大小 1000
		CombinationCount: 100,  // 默认组合数 100
		DecisionWait:     30 * time.Second,
	}
}

func createTracesProcessor(
	ctx context.Context,
	params processor.Settings,
	cfg component.Config,
	nextConsumer consumer.Traces,
) (processor.Traces, error) {
	tCfg := cfg.(*Config)

	// if telemetry.IsRecordPolicyEnabled() {
	// 	tCfg.Options = append(tCfg.Options, withRecordPolicy())
	// }
	return newTracesProcessor(ctx, params, nextConsumer, *tCfg)
}
