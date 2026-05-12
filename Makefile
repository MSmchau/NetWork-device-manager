.PHONY: dev prod update restart-backend

dev:  ## 开发模式启动（代码修改热重载，无需重建镜像）
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

prod:  ## 生产模式启动（需 --build 重建镜像）
	docker compose up -d --build

update:  ## 拉取代码 + 重启后端（前端变更需 make dev）
	git pull
	docker compose -f docker-compose.yml -f docker-compose.dev.yml restart backend
	@echo "========================================"
	@echo " 后端已重启（热重载模式）"
	@echo " 若前端文件有变更，请执行: make dev"
	@echo "========================================"

restart-backend:  ## 仅重启后端（拉取代码后使用）
	docker compose restart backend
	@echo "后端已重启"
