import asyncio

async def risky_operation():
    await asyncio.sleep(2)
    raise ValueError("Something went wrong inside the task!")

async def delay_task():
    await asyncio.sleep(5)
    return "2 seconds have passed"

async def main():
    # Start the coroutine as a task
    task = asyncio.create_task(risky_operation())
    task2 = asyncio.create_task(delay_task())

    # Do other work while task runs
    print("Task started... doing other work")

    # Now await the task to retrieve its exception
    try:
        task.cancel()  # This will raise the exception from risky_operation
        result = await task2
        await task
        print("Task result:", result)
    except Exception as e:
        print("Caught exception from task:", e)

asyncio.run(main())
