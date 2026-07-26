package scheduler

import (
	"context"
	"testing"

	"github.com/m1kus3q/pubpredictor/backend/internal/scheduler/mocks"
	"github.com/robfig/cron/v3"

	"github.com/stretchr/testify/require"
	"go.uber.org/mock/gomock"
)

type mockJob struct{}

func (m *mockJob) Run(ctx context.Context) {}

func TestAddJobWithCron(t *testing.T) {
	scheduler := NewScheduler()
	job := &mockJob{}

	scheduler.AddJob(job, ("0 6 * * *"))

	require.Len(t, scheduler.jobs, 1)

	require.Equal(t, "0 6 * * *", scheduler.jobs[0].cronTime)
	require.Same(t, job, scheduler.jobs[0].run)
}

func TestStartStopLifecycle(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	cronMock := mocks.NewMockCron(ctrl)

	scheduler := &Scheduler{
		cron: cronMock,
		jobs: []Job{
			{
				cronTime: "@daily",
				run:      &mockJob{},
			},
			{
				cronTime: "@hourly",
				run:      &mockJob{},
			},
		},
	}

	cronMock.EXPECT().
		AddFunc("@daily", gomock.Any()).
		Return(cron.EntryID(1), nil)

	cronMock.EXPECT().
		AddFunc("@hourly", gomock.Any()).
		Return(cron.EntryID(2), nil)

	cronMock.EXPECT().Start()
	scheduler.Start()

	cronMock.EXPECT().Stop().Return(context.Background())

	require.Nil(t, scheduler.jobs)

	scheduler.Stop()
}

type panicJob struct{}

func (p *panicJob) Run(ctx context.Context) {
	panic("boom")
}

func TestRunJobRecoverPanic(t *testing.T) {
	scheduler := &Scheduler{}

	require.NotPanics(t, func() {
		scheduler.runJob(&panicJob{})
	})
}
