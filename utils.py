import asyncio


class GitUtil:
    def __init__(self, manager):
        self.manager = manager
        self.app = self.manager.app

    async def get_commit_hash(self, remote=True):
        branch = self.manager.branch
        repo_path = self.manager.repo
        source = f"origin/{branch}" if remote else branch
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            repo_path,
            "show",
            source,
            "--format=%H",
            "-s",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode().strip()
        else:
            raise RuntimeError(f"Git error: {stderr.decode().strip()}")

    async def get_changed_files(self):
        path = self.manager.repo
        current_hash = self.manager.current_hash
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            path,
            "diff",
            "--name-only",
            f"{current_hash}..HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            changed_files = stdout.decode().strip().split("\n")
            return changed_files
        else:
            raise RuntimeError(f"Git error: {stderr.decode().strip()}")

    async def git_pull(repo_path):
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            repo_path,
            "pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode().strip()
        else:
            raise RuntimeError(f"Git error: {stderr.decode().strip()}")
