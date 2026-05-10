import asyncio
import time

from clawteam.scheduler import ClawTeamScheduler
from agencies.dispatcher import dispatch, run_task
from agencies.base import Task


async def stress_test():
    scheduler = ClawTeamScheduler()
    tasks = []
    for i in range(10):
        desc = f'生成第{i + 1}篇小红书AI副业内容'
        agency_id = dispatch(desc, 'content_creation')
        task = Task(task_id=f'test_{{i}}', task_type='content_creation', payload={'topic': 'AI副业'})
        tasks.append({'fn': lambda t=task, aid=agency_id: run_task(aid, t), 'type': 'content_gen'})

    start = time.time()
    results = await scheduler.run_parallel(tasks)
    print(f'✅ 10个并发任务完成，总耗时 {time.time() - start:.2f}s')
    return results


if __name__ == '__main__':
    asyncio.run(stress_test())
