from contextlib import asynccontextmanager

from aiopath import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from panel.io.fastapi import add_applications

from .utils import GitUtil

BRANCH = "main"
REPO = "/opt/reporting/test-reports"


class Manager:
    def __init__(self, app):
        self.app = app
        self.branch = BRANCH
        self.repo = REPO
        self.routes = {}  # {k:f"{self.repo}/{v}" for k,v in ROUTES.items}
        self.notebooks = {}  # {v:k for k,v in ROUTES.items}
        self.git = GitUtil(self)
        self.scheduler = AsyncIOScheduler()
        self.current_hash = None

    async def start(self):
        async for path in Path(REPO).rglob("*.ipynb"):
            self.add_route_for_path(path)
        self.current_hash = await self.git.get_commit_hash(remote=False)
        self.scheduler.start()
        app.state.scheduler.add_job(
            self.check_for_updates, "interval", seconds=10, args=[app]
        )

    async def add_route_for_path(self, path):
        if not path.is_relative_to(self.repo):
            print("Cannot add a route for a path that is not in my local repo")
            return
        slug = str(path.relative_to(self.repo).with_suffix(""))
        self.routes[slug] = await path.resolve()
        self.notebooks[str(path)] = slug
        add_applications({slug: self.routes[slug]})

    async def check_for_updates(self):
        if await self.git.get_commit_hash() != self.current_hash:
            await self.git.pull()
            changed_files = await self.git.get_changed_files()
            self.current_hash = await self.git.get_commit_hash(remote=False)
            for file in changed_files:
                if file in self.notebooks:
                    await self.reload_route(self.notebooks[file])
                else:
                    self.add_route_for_path(Path(file))

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
    app.state.scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
