#!/usr/bin/env bash
# new_api_module.sh — создать заготовку FastAPI-модуля (routes + schemas) и подключить его в routes/__init__.py
# Использование: ./tools/new_api_module.sh <module_name>
set -euo pipefail

# ---------- helpers ----------
err() { echo "Error: $*" >&2; exit 1; }

# sed -i совместимость macOS/Linux
sedi() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"
  else
    # BSD sed (macOS) — требуется пустой суффикс для -i
    local file="${@: -1}"
    local args=("${@:1:$(($#-1))}")
    sed -i '' "${args[@]}" "$file"
  fi
}

to_pascal_case() {
  local s="$1"
  # заменим все не [a-zA-Z0-9_] на _
  s="${s//[^a-zA-Z0-9_]/_}"
  local IFS='_'
  read -ra parts <<< "$s"
  local out=""
  for p in "${parts[@]}"; do
    [[ -z "$p" ]] && continue
    local first="${p:0:1}"
    local rest="${p:1}"
    out+="${first^^}${rest,,}"
  done
  echo "$out"
}

# ---------- args & paths ----------
[[ $# -ge 1 ]] || err "Укажите имя модуля. Пример: ./tools/new_api_module.sh orders"
NAME_RAW="$1"

# валидация имени для python-модуля
[[ "$NAME_RAW" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || err "Недопустимое имя модуля: $NAME_RAW"

ROOT="src/fastapi_app"
ROUTES="$ROOT/routes"
SCHEMAS="$ROOT/schemas"
INIT_FILE="$ROUTES/__init__.py"

[[ -d "$ROOT" ]]   || err "Не найдено $ROOT — запусти из корня проекта."
[[ -d "$ROUTES" ]] || err "Не найдено $ROUTES"
[[ -d "$SCHEMAS" ]]|| err "Не найдено $SCHEMAS"
[[ -f "$INIT_FILE" ]] || err "Не найден $INIT_FILE"

NAME_PASCAL="$(to_pascal_case "$NAME_RAW")"
ROUTE_FILE="$ROUTES/${NAME_RAW}.py"
SCHEMA_FILE="$SCHEMAS/${NAME_RAW}.py"

IMPORT_LINE="from ..routes.${NAME_RAW} import router as ${NAME_RAW}_router"
INCLUDE_LINE="api.include_router(${NAME_RAW}_router)"

# ---------- create schema file ----------
if [[ ! -f "$SCHEMA_FILE" ]]; then
  cat > "$SCHEMA_FILE" <<PY
from pydantic import BaseModel

class ${NAME_PASCAL}Out(BaseModel):
    id: int
    name: str
PY
  echo "Создано: $SCHEMA_FILE"
else
  echo "Пропуск: $SCHEMA_FILE уже существует"
fi

# ---------- create route file ----------
if [[ ! -f "$ROUTE_FILE" ]]; then
  cat > "$ROUTE_FILE" <<PY
from fastapi import APIRouter
from ..schemas.${NAME_RAW} import ${NAME_PASCAL}Out

router = APIRouter()

@router.get("/${NAME_RAW}", response_model=list[${NAME_PASCAL}Out], tags=["${NAME_RAW}"])
def list_${NAME_RAW}():
    # TODO: реализовать бизнес-логику
    return []
PY
  echo "Создано: $ROUTE_FILE"
else
  echo "Пропуск: $ROUTE_FILE уже существует"
fi

# ---------- ensure import present in __init__.py ----------
if ! grep -qE "^\s*${IMPORT_LINE}\s*$" "$INIT_FILE"; then
  # вставим импорт после существующих импортов или в начало
  # если первая строка начинается не с 'from'/'import' — просто добавим в начало
  if head -n1 "$INIT_FILE" | grep -qE "^(from|import)\b"; then
    # найдём последний импорт и вставим после него
    awk -v imp="${IMPORT_LINE}" '
      BEGIN{added=0}
      {
        print \$0
        if (\$0 ~ /^(from|import)[[:space:]]/){ last_import=NR }
      }
      END{
        # awk не изменяет файл, вставим позже sed-ом
      }' "$INIT_FILE" >/dev/null
    # вставка после последней строки с импортом
    line_num=$(nl -ba "$INIT_FILE" | sed -n '/^\s*[0-9]\+\s\+\(from\|import\)\b/ h; ${x;p;}' | awk '{print $1}')
    if [[ -n "${line_num:-}" ]]; then
      sedi "${line_num}a\\
${IMPORT_LINE}
" "$INIT_FILE"
    else
      # fallback — в начало
      sedi "1i ${IMPORT_LINE}" "$INIT_FILE"
    fi
  else
    sedi "1i ${IMPORT_LINE}" "$INIT_FILE"
  fi
  echo "Добавлен импорт в $INIT_FILE"
else
  echo "Импорт уже есть в $INIT_FILE"
fi

# ---------- ensure include present before app.include_router(api) ----------
if ! grep -qE "^\s*${INCLUDE_LINE}\s*$" "$INIT_FILE"; then
  # найдём строку с app.include_router(api)
  if grep -qE "app\.include_router\(api\)" "$INIT_FILE"; then
    # вставим include перед этой строкой (с отступом в 4 пробела)
    sedi "s|app\.include_router(api)|${INCLUDE_LINE}\n    app.include_router(api)|" "$INIT_FILE"
    echo "Подключён роутер в $INIT_FILE"
  else
    # если такой строки нет — попробуем после создания api = APIRouter(...)
    if grep -qE "api\s*=\s*APIRouter" "$INIT_FILE"; then
      # вставим после строки с созданием api
      line_api=$(nl -ba "$INIT_FILE" | sed -n '/api\s*=\s*APIRouter/p' | awk '{print $1}' | tail -n1)
      [[ -n "${line_api:-}" ]] && sedi "$((line_api+1))a\\
    ${INCLUDE_LINE}
" "$INIT_FILE"
      echo "Подключён роутер после объявления api в $INIT_FILE"
    else
      # крайний случай — добавим в конец файла (но до return сборки)
      echo -e "\n${INCLUDE_LINE}" >> "$INIT_FILE"
      echo "Подключён роутер (append) в $INIT_FILE"
    fi
  fi
else
  echo "Подключение роутера уже есть в $INIT_FILE"
fi

echo "Готово: модуль '${NAME_RAW}' создан и подключён."
echo "Перезапусти FastAPI (если нужно): docker compose restart fastapi"
