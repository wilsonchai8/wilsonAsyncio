from wilsonasyncio import run

async def hello():
    print('enter hello ...')
    return 'return world ...'

if __name__ == "__main__":
    ret = run(hello())
    print(ret)