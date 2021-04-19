from pymake import *
import glob

MPY = 'firmware/micropython'

with env(
    USER_C_MODULES='firmware/ulab',
    FROZEN_MANIFEST='frozen_manifest.py',
    ESPIDF='firmware/esp-idf',
    PATH=f'firmware/xtensa-esp32-elf/bin:{PATH}'
):
    qstr_defs = mpy_cross = Makefile(f'{MPY}/mpy-cross')

    @makes('firmware/bytecode/%.mpy', ['src/%.py', mpy_cross])
    async def _bytecode(out: Path, deps: Dependencies):
        src, _ = deps
        out.mkdir(parents=True, exist_ok=True)
        await sh(f"${MPY}/mpy-cross/mpy-cross -O 3 -o {out} {src}")

    all_bytecode = Group([
        _bytecode(path) for path in glob.iglob("src/**/*.py")
    ])
    print(all_bytecode)


if __name__ == "__main__":
    cli(__file__, loglevel="DEBUG")
