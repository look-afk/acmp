from pathlib import Path
import re
import shutil
import sys

# ROOT указывает на корень проекта ACMP (на один уровень выше папки tools)
ROOT = Path(__file__).parent.parent.resolve()
BACKUP_ROOT = ROOT / ".acmp_backup"


def create_task_files(fill_file: Path) -> None:
    letter = fill_file.read_text(encoding="utf-8").strip().upper()

    if not re.fullmatch(r"[A-Z]", letter):
        print(f"Skipped {fill_file}: expected one letter A-Z, got {letter!r}")
        return

    for code in range(ord("A"), ord(letter) + 1):
        task_file = fill_file.parent / f"{chr(code)}.py"
        if not task_file.exists():
            task_file.touch()
            print(f"Created {task_file}")

    fill_file.unlink()
    print(f"Deleted {fill_file}")


def backup_folder(folder: Path) -> None:
    backup_dir = BACKUP_ROOT / folder.relative_to(ROOT)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True)

    for item in folder.iterdir():
        # НЕ копируем файлы-триггеры в бэкап
        if item == backup_dir or item.name in ["refill.py", "backup.py", "Fill.py"]:
            continue
            
        target = backup_dir / item.name
        if item.is_dir() and not item.is_symlink():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def refill_folder(refill_file: Path) -> None:
    backup_folder(refill_file.parent)

    for item in refill_file.parent.iterdir():
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()

    print(f"Backed up and deleted all contents of {refill_file.parent}")


def restore_folder(backup_file: Path) -> None:
    target_folder = backup_file.parent
    backup_dir = BACKUP_ROOT / target_folder.relative_to(ROOT)

    if not backup_dir.exists():
        print(f"No backup found for {target_folder}")
        backup_file.unlink(missing_ok=True)
        return

    for item in backup_dir.iterdir():
        target = target_folder / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    backup_file.unlink(missing_ok=True)
    print(f"Restored contents to {target_folder}")


if __name__ == '__main__':
    # 1. Ищем и обрабатываем Fill.py
    for fill_file in ROOT.rglob("Fill.py"):
        if "tools" in fill_file.parts or ".acmp_backup" in fill_file.parts:
            continue
        create_task_files(fill_file)

    # 2. Ищем и обрабатываем refill.py
    for refill_file in ROOT.rglob("refill.py"):
        if "tools" in refill_file.parts or ".acmp_backup" in refill_file.parts:
            continue
        refill_folder(refill_file)

    # 3. Ищем и обрабатываем backup.py
    for backup_file in ROOT.rglob("backup.py"):
        if backup_file.resolve() == Path(__file__).resolve():
            continue
        if "tools" in backup_file.parts or ".acmp_backup" in backup_file.parts:
            continue
        restore_folder(backup_file)

