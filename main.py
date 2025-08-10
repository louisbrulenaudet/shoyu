import asyncio

from src.shoyu import AsyncShoyu


async def main() -> None:
    """
    Run asynchronous web searches using AsyncWebSearch.

    This function demonstrates how to use AsyncWebSearch with the required parameters.
    It performs 20 search queries and prints the results, error count, and success rate.

    Returns:
        None

    Example:
        >>> asyncio.run(main())
        Result 1: ...
        ...
        Total errors: 0
        Success rate: 100.00%
    """
    errors = 0

    async with AsyncShoyu(num_circuits=5, max_queries_per_identity=10) as search:
        for i in range(20):
            try:
                result = await search("orcinus orca description")
                print(f"Result {i + 1}: {result}")
            except Exception as e:
                print(f"Error on query {i + 1}: {e}")
                errors += 1

        print(f"Total errors: {errors}")
        print(f"Success rate: {100 * (20 - errors) / 20:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
