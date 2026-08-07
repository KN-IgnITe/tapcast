//go:build integration

package scheduler

import (
	"context"
	"sync/atomic"
	"testing"
	"time"

	"github.com/robfig/cron/v3"
	"github.com/stretchr/testify/require"
)

type testJob struct {
	called atomic.Bool
}

func (j *testJob) Run(ctx context.Context) {
	j.called.Store(true)
}

func TestSchedulerRunJob(t *testing.T) {
	job := &testJob{}

	scheduler := &Scheduler{
		cron: cron.New(),
	}

	scheduler.AddJob(job, "@every 1s")

	require.NoError(t, scheduler.Start())
	defer scheduler.Stop()

	require.Eventually(t, func() bool {
		return job.called.Load()
	}, 5*time.Second, 100*time.Millisecond)
}
