package scheduler

import (
	"context"
	"log"
	"time"

	"github.com/robfig/cron/v3"
)

const JobTimeout = 30 * time.Second

type RunnableJob interface {
	Run(ctx context.Context)
}

//go:generate mockgen -source=scheduler.go -destination=./mocks/scheduler_mock.go -package=mocks
type Cron interface {
	AddFunc(spec string, cmd func()) (cron.EntryID, error)
	Start()
	Stop() context.Context
}

type Job struct {
	cronTime string
	run      RunnableJob
}

type Scheduler struct {
	cron Cron
	jobs []Job
}

func (s *Scheduler) runJob(job RunnableJob) func() {
	return func() {
		defer func() {
			if r := recover(); r != nil {
				log.Printf("job panicked: %v", r)
			}
		}()
		ctx, cancel := context.WithTimeout(context.Background(), JobTimeout)
		defer cancel()

		job.Run(ctx)
	}
}

func NewScheduler() *Scheduler {
	return &Scheduler{
		cron: cron.New(),
		jobs: nil,
	}
}

func (s *Scheduler) AddJob(runJob RunnableJob, cronTime string) {
	s.jobs = append(s.jobs, Job{
		cronTime: cronTime,
		run:      runJob,
	})
}

func (s *Scheduler) Start() error {
	for _, job := range s.jobs {
		_, err := s.cron.AddFunc(job.cronTime, s.runJob(job.run))
		if err != nil {
			return err
		}
	}

	// Prevent duplicate job registration.
	s.jobs = nil

	s.cron.Start()
	return nil
}

func (s *Scheduler) Stop() context.Context {
	return s.cron.Stop()
}

/*

"feature(sheduler): add weather job to save forecast"
"feature(sheduler): add sheduler "


*/
