from wilsonasyncio import get_event_loop

async def hello():
    print('enter hello ...')
    return 'return world ...'

if __name__ == "__main__":
    loop = get_event_loop()
    task = loop.create_task(hello())
    rst = loop.run_until_complete(task)
    print(rst)

