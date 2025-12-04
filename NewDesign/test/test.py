import asyncio
import asyncio_redis


async def example():
    # Create Redis connection
    connection = await asyncio_redis.Connection.create(host="127.0.0.1", port=6379)
    queueName = "datastore:queue:queue_20_67"
    # Set a key
    await connection.lpush(queueName, ['task1'])
    await connection.lpush(queueName, ['task2'])
    await connection.lpush(queueName, ['task3'])

    print("Values pushed to 'queueName'.")

    # LRANGE: Retrieve all elements from the list
    values = await connection.lrange(queueName, 0, -1)
    print("Current list contents:", values)

    # pop all one by one
    while True:
        try:
            value = await connection.brpop([queueName],timeout=1)
        except Exception as e:
            print("Error popping value:", e)
            break

        print("Popped value:", value)

    # When finished, close the connection.
    connection.close()


if __name__ == "__main__":
    asyncio.run(example())
