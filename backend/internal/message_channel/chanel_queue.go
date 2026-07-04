package message_channel

type MessageQueue interface {
	Publish(job string) error
	Subscribe() (<-chan string, error)
}

type LocalQueue struct {
	jobs chan string
}

func NewLocalQueue(size int) *LocalQueue {
	return &LocalQueue{
		jobs: make(chan string, size),
	}
}

func (q *LocalQueue) Publish(job string) error {
	q.jobs <- job
	return nil
}

func (q *LocalQueue) Subscribe() (<-chan string, error) {
	return q.jobs, nil
}
