import asyncio


class GitUtil:
    def __init__(self, manager):
        self.manager = manager
        self.app = self.manager.app

    async def get_commit_hash(self, remote=True):
        branch = self.manager.branch
        if remote:
            await self.fetch()
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            self.manager.repo_str,
            "show",
            f"origin/{branch}" if remote else branch,
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
        path = self.manager.repo_str
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

    async def pull(self):
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            self.manager.repo_str,
            "pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode().strip()
        else:
            raise RuntimeError(f"Git error: {stderr.decode().strip()}")

    async def fetch(self):
        repo_path = self.manager.repo_str
        branch = self.manager.branch

        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            repo_path,
            "fetch",
            "--quiet",
            "origin",
            branch,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()

        if process.returncode != 0:
            raise RuntimeError("Failed to fetch remote branch")
