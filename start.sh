#!/bin/bash
# Docker Compose 快捷启动脚本
# 用法: ./start.sh [dev|build|down|logs]

case "${1:-}" in
    dev)
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        ;;
    build)
        docker-compose up -d --build
        ;;
    down)
        docker-compose down
        ;;
    logs)
        docker-compose logs -f
        ;;
    *)
        docker-compose up -d
        ;;
esac
