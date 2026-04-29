if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Помилка: {e}")
