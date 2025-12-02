import asyncio
import asyncio_redis


async def example():
    # Create Redis connection
    connection = await asyncio_redis.Connection.create(host="127.0.0.1", port=6379)

    # Set a key
    data = await connection.get("my_key")
    print(data)
    await connection.set("my_key", "my_value1")

    # When finished, close the connection.
    connection.close()


if __name__ == "__main__":
    asyncio.run(example())
