from contextlib import asynccontextmanager

from aiopath import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from panel.io.fastapi import add_applications

from utils import GitUtil

BRANCH = "main"
REPO = "/opt/reports/"


class Manager:
    def __init__(self, app):
        self.app = app
        self.branch = BRANCH
        self.repo_str = REPO
        self.repo_path = Path(self.repo_str)
        self.routes = {}  # {k:f"{self.repo_str}/{v}" for k,v in ROUTES.items}
        self.notebooks = {}  # {v:k for k,v in ROUTES.items}
        self.git = GitUtil(self)
        self.scheduler = AsyncIOScheduler()
        self.current_hash = None

    async def start(self):
        async for path in Path(REPO).rglob("*.ipynb"):
            await self.add_route_for_path(path)
        self.current_hash = await self.git.show(remote=False)
        self.scheduler.start()
        self.scheduler.add_job(self.check_for_updates, "interval", seconds=10)

    async def shutdown(self):
        self.scheduler.shutdown()

    async def add_route_for_path(self, path):
        if not path.is_relative_to(self.repo_str):
            # then the path came from git diff and doesn't contain relation info
            if not await (self.repo_path / str(path)).is_file():
                print(f"Cannot add a route for {path} which is not in my local repo")
                return
            else:
                print(f"The path {path} is in my repo!")
            slug = str(path.with_suffix(""))
        else:
            slug = str(path.relative_to(self.repo_str).with_suffix(""))
        slug = "/" + slug
        self.routes[slug] = await path.resolve()
        self.notebooks[str(path)] = slug
        print(f"Adding route {slug} for notebook {path}")
        add_applications({slug: self.routes[slug]}, app=self.app)

    async def check_for_updates(self):
        remote_hash = await self.git.show()
        if remote_hash != self.current_hash:
            print("Remote repo was updated! Pulling.")
            await self.git.pull()
            changed_files = await self.git.diff()
            self.current_hash = await self.git.show(remote=False)
            for file in changed_files:
                if file in self.notebooks:
                    await self.reload_route(self.notebooks[file])
                else:
                    await self.add_route_for_path(Path(file))

    async def reload_route(self, slug):
        to_remove = []
        for route in app.router.routes:
            if route.path.startswith(slug):
                to_remove.append(route)
        for route in to_remove:
            app.router.routes.remove(route)
        add_applications({slug: self.routes[slug]}, app=app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.manager = Manager(app)
    await app.state.manager.start()
    yield
    print("Shutting down...")
    await app.state.manager.shutdown()


app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
