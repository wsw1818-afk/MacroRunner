"""
매크로 데이터 관리자
JSON 기반 매크로 저장, 로드, 검색, 카테고리 관리
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
import re

from ..utils.constants import (
    MACROS_DIR, BACKUPS_DIR, MACRO_INDEX_FILE,
    PACKAGE_MACROS_DIR, IS_FROZEN, DEFAULT_CATEGORIES, BACKUP_SETTINGS
)


@dataclass
class Macro:
    """매크로 데이터 클래스"""
    name: str
    code: str
    program: str  # "excel", "ppt", "word"
    description: str = ""
    category: str = "일반"
    favorite: bool = False
    use_count: int = 0
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    version: int = 1
    history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict, name: str = None, program: str = None) -> "Macro":
        """딕셔너리에서 매크로 생성 (이전 버전 호환)"""
        # 이전 버전 데이터 호환
        if "name" not in data and name:
            data["name"] = name
        if "program" not in data and program:
            data["program"] = program

        # 필수 필드 기본값
        defaults = {
            "description": "",
            "category": "일반",
            "favorite": False,
            "use_count": 0,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "last_used": None,
            "version": 1,
            "history": []
        }

        for key, default in defaults.items():
            if key not in data:
                data[key] = default

        return cls(**data)


class MacroManager:
    """매크로 관리자 - CRUD 및 검색 기능"""

    def __init__(self):
        self._reset_state()
        self._on_change_callbacks: List[Callable] = []
        self._last_state: Optional[str] = None  # 마지막 상태 (undo용)

        self._ensure_directories()
        self.load()

    def _reset_state(self):
        """메모리 상태 초기화"""
        self._macros: Dict[str, Dict[str, Macro]] = {
            "excel": {},
            "ppt": {},
            "word": {}
        }
        self._categories: List[str] = list(DEFAULT_CATEGORIES)

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        MACROS_DIR.mkdir(parents=True, exist_ok=True)
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        default_index = PACKAGE_MACROS_DIR / "macro_index.json"
        if IS_FROZEN and default_index.exists():
            if not MACRO_INDEX_FILE.exists():
                shutil.copy(default_index, MACRO_INDEX_FILE)
            else:
                self._sync_packaged_defaults(default_index)

    def _sync_packaged_defaults(self, default_index: Path):
        """EXE 패키지 기본 매크로가 더 최신이면 사용자 사본에 병합"""
        try:
            with open(default_index, "r", encoding="utf-8") as f:
                packaged_data = json.load(f)
            with open(MACRO_INDEX_FILE, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except Exception:
            return

        changed = False

        user_categories = user_data.setdefault("_categories", [])
        for category in packaged_data.get("_categories", []):
            if category not in user_categories:
                user_categories.append(category)
                changed = True

        for program in ["excel", "ppt", "word"]:
            packaged_macros = packaged_data.get(program, {})
            user_macros = user_data.setdefault(program, {})

            for name, packaged_macro in packaged_macros.items():
                user_macro = user_macros.get(name)
                if user_macro is None:
                    user_macros[name] = packaged_macro
                    changed = True
                    continue

                if self._is_packaged_macro_newer(packaged_macro, user_macro):
                    user_macros[name] = self._merge_packaged_macro(
                        packaged_macro, user_macro
                    )
                    changed = True

        if changed:
            with open(MACRO_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _is_packaged_macro_newer(packaged_macro: Dict, user_macro: Dict) -> bool:
        packaged_modified = MacroManager._parse_datetime(packaged_macro.get("modified"))
        user_modified = MacroManager._parse_datetime(user_macro.get("modified"))

        if packaged_modified and user_modified and user_modified > packaged_modified:
            return False

        packaged_version = MacroManager._safe_int(packaged_macro.get("version"))
        user_version = MacroManager._safe_int(user_macro.get("version"))

        if packaged_version > user_version:
            return True

        if packaged_modified and user_modified:
            return packaged_modified > user_modified

        return False

    @staticmethod
    def _merge_packaged_macro(packaged_macro: Dict, user_macro: Dict) -> Dict:
        merged = dict(packaged_macro)

        for key in ["favorite", "use_count", "last_used", "created"]:
            if key in user_macro:
                merged[key] = user_macro[key]

        history = list(user_macro.get("history", []))
        if user_macro.get("code") and user_macro.get("code") != packaged_macro.get("code"):
            history.append({
                "version": user_macro.get("version", 1),
                "modified": user_macro.get("modified"),
                "code": user_macro.get("code")
            })
        if history:
            merged["history"] = history

        return merged

    @staticmethod
    def _safe_int(value, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def load(self) -> bool:
        """매크로 데이터 로드"""
        try:
            self._reset_state()

            if not MACRO_INDEX_FILE.exists():
                self._create_default_file()
                return True

            with open(MACRO_INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 이전 버전 형식 변환
            for program in ["excel", "ppt", "word"]:
                if program in data:
                    for name, macro_data in data[program].items():
                        self._macros[program][name] = Macro.from_dict(
                            macro_data, name=name, program=program
                        )

            # 카테고리 로드
            if "_categories" in data:
                self._categories = data["_categories"]

            return True

        except Exception as e:
            print(f"매크로 로드 오류: {e}")
            return False

    def save(self, create_backup: bool = True) -> bool:
        """매크로 데이터 저장"""
        try:
            # 백업 생성
            if create_backup and BACKUP_SETTINGS["on_save"]:
                self._create_backup()

            # 데이터 준비
            data = {"_categories": self._categories}
            for program in ["excel", "ppt", "word"]:
                data[program] = {}
                for name, macro in self._macros[program].items():
                    data[program][name] = macro.to_dict()

            # 저장
            with open(MACRO_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._notify_change("save")
            return True

        except Exception as e:
            print(f"매크로 저장 오류: {e}")
            return False

    def _create_default_file(self):
        """기본 매크로 파일 생성"""
        data = {
            "_categories": DEFAULT_CATEGORIES,
            "excel": {},
            "ppt": {},
            "word": {}
        }
        with open(MACRO_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _create_backup(self):
        """백업 생성"""
        if not MACRO_INDEX_FILE.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUPS_DIR / f"macro_index_{timestamp}.json"

        shutil.copy(MACRO_INDEX_FILE, backup_file)

        # 오래된 백업 삭제
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        """오래된 백업 파일 정리"""
        backups = sorted(BACKUPS_DIR.glob("macro_index_*.json"), reverse=True)
        max_backups = BACKUP_SETTINGS["max_backups"]

        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except Exception:
                pass

    # CRUD Operations

    def add(self, macro: Macro) -> bool:
        """매크로 추가"""
        program = macro.program
        name = macro.name

        if name in self._macros[program]:
            return False  # 이미 존재

        self._macros[program][name] = macro
        self._notify_change("add", macro)
        return True

    def update(self, macro: Macro, save_history: bool = True) -> bool:
        """매크로 업데이트"""
        program = macro.program
        name = macro.name

        if name not in self._macros[program]:
            return False

        old_macro = self._macros[program][name]

        # 버전 기록 (동일 객체 참조 문제 해결을 위해 기존 히스토리 복사)
        if save_history and old_macro is not macro:
            # 다른 객체일 경우 기존 로직
            history_entry = {
                "version": old_macro.version,
                "code": old_macro.code,
                "modified": old_macro.modified
            }
            macro.history = list(old_macro.history) + [history_entry]
            macro.version = old_macro.version + 1
        elif save_history:
            # 동일 객체일 경우 (직접 수정 후 update 호출)
            # 히스토리에서 이전 코드 추출
            if macro.history:
                last_version = macro.version
                last_code = macro.history[-1]["code"] if macro.history else macro.code
            else:
                last_version = macro.version
                last_code = macro.code

            # 새 버전 번호 부여
            macro.version = last_version + 1

        macro.modified = datetime.now().isoformat()
        self._macros[program][name] = macro
        self._notify_change("update", macro)
        return True

    def delete(self, program: str, name: str) -> bool:
        """매크로 삭제"""
        if name not in self._macros[program]:
            return False

        del self._macros[program][name]
        self._notify_change("delete", {"program": program, "name": name})
        return True

    def get(self, program: str, name: str) -> Optional[Macro]:
        """매크로 가져오기"""
        return self._macros[program].get(name)

    def get_all(self, program: str = None) -> List[Macro]:
        """모든 매크로 가져오기"""
        if program:
            return list(self._macros[program].values())

        all_macros = []
        for prog_macros in self._macros.values():
            all_macros.extend(prog_macros.values())
        return all_macros

    def rename(self, program: str, old_name: str, new_name: str) -> bool:
        """매크로 이름 변경"""
        if old_name not in self._macros[program]:
            return False
        if new_name in self._macros[program]:
            return False

        macro = self._macros[program][old_name]
        macro.name = new_name
        macro.modified = datetime.now().isoformat()

        del self._macros[program][old_name]
        self._macros[program][new_name] = macro

        self._notify_change("rename", {"old": old_name, "new": new_name})
        return True

    def duplicate(self, program: str, name: str, new_name: str = None) -> Optional[Macro]:
        """매크로 복제"""
        original = self.get(program, name)
        if not original:
            return None

        # 새 이름 생성
        if not new_name:
            counter = 1
            new_name = f"{name} (복사본)"
            while new_name in self._macros[program]:
                counter += 1
                new_name = f"{name} (복사본 {counter})"

        # 복제본 생성
        duplicate = Macro(
            name=new_name,
            code=original.code,
            program=program,
            description=original.description,
            category=original.category,
            favorite=False,
            use_count=0,
            created=datetime.now().isoformat(),
            modified=datetime.now().isoformat()
        )

        self.add(duplicate)
        return duplicate

    # Search & Filter

    def search(self, query: str, program: str = None) -> List[Macro]:
        """매크로 검색 (이름, 코드, 설명)"""
        query = query.lower()
        results = []

        macros = self.get_all(program)
        for macro in macros:
            if (query in macro.name.lower() or
                query in macro.code.lower() or
                query in macro.description.lower()):
                results.append(macro)

        return results

    def filter_by_category(self, category: str, program: str = None) -> List[Macro]:
        """카테고리별 필터"""
        macros = self.get_all(program)
        return [m for m in macros if m.category == category]

    def get_favorites(self, program: str = None) -> List[Macro]:
        """즐겨찾기 목록"""
        macros = self.get_all(program)
        return [m for m in macros if m.favorite]

    def get_recent(self, program: str = None, limit: int = 10) -> List[Macro]:
        """최근 사용 매크로"""
        macros = self.get_all(program)
        used = [m for m in macros if m.last_used]
        used.sort(key=lambda m: m.last_used, reverse=True)
        return used[:limit]

    def get_most_used(self, program: str = None, limit: int = 10) -> List[Macro]:
        """가장 많이 사용한 매크로"""
        macros = self.get_all(program)
        macros.sort(key=lambda m: m.use_count, reverse=True)
        return macros[:limit]

    # Favorites & Usage

    def toggle_favorite(self, program: str, name: str) -> bool:
        """즐겨찾기 토글"""
        macro = self.get(program, name)
        if not macro:
            return False

        macro.favorite = not macro.favorite
        macro.modified = datetime.now().isoformat()
        self._notify_change("favorite", macro)
        return macro.favorite

    def record_usage(self, program: str, name: str):
        """사용 기록"""
        macro = self.get(program, name)
        if macro:
            macro.use_count += 1
            macro.last_used = datetime.now().isoformat()

    # Categories

    def get_categories(self) -> List[str]:
        """카테고리 목록"""
        return list(self._categories)

    def add_category(self, category: str) -> bool:
        """카테고리 추가"""
        if category in self._categories:
            return False
        self._categories.append(category)
        self._notify_change("category_add", category)
        return True

    def remove_category(self, category: str) -> bool:
        """카테고리 제거"""
        if category not in self._categories or category == "일반":
            return False
        self._categories.remove(category)
        self._notify_change("category_remove", category)
        return True

    # Version History

    def get_history(self, program: str, name: str) -> List[Dict]:
        """매크로 버전 히스토리"""
        macro = self.get(program, name)
        if not macro:
            return []
        return macro.history

    def restore_version(self, program: str, name: str, version: int) -> bool:
        """특정 버전으로 복원"""
        macro = self.get(program, name)
        if not macro:
            return False

        for hist in macro.history:
            if hist["version"] == version:
                # 현재 버전을 히스토리에 추가
                current_hist = {
                    "version": macro.version,
                    "code": macro.code,
                    "modified": macro.modified
                }
                macro.history.append(current_hist)
                macro.version += 1

                # 복원
                macro.code = hist["code"]
                macro.modified = datetime.now().isoformat()
                self._notify_change("restore", macro)
                return True

        return False

    # Export / Import

    def export_macros(self, filepath: str, program: str = None, names: List[str] = None) -> bool:
        """매크로 내보내기"""
        try:
            data = {"_version": "2.0", "_categories": self._categories}

            if program and names:
                # 선택된 매크로만
                data[program] = {}
                for name in names:
                    macro = self.get(program, name)
                    if macro:
                        data[program][name] = macro.to_dict()
            elif program:
                # 프로그램 전체
                data[program] = {n: m.to_dict() for n, m in self._macros[program].items()}
            else:
                # 전체
                for prog in ["excel", "ppt", "word"]:
                    data[prog] = {n: m.to_dict() for n, m in self._macros[prog].items()}

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"내보내기 오류: {e}")
            return False

    def import_macros(self, filepath: str, overwrite: bool = False) -> Tuple[int, int]:
        """매크로 가져오기 - (성공 수, 스킵 수) 반환"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            success = 0
            skipped = 0

            for program in ["excel", "ppt", "word"]:
                if program not in data:
                    continue

                for name, macro_data in data[program].items():
                    if name in self._macros[program] and not overwrite:
                        skipped += 1
                        continue

                    macro = Macro.from_dict(macro_data, name=name, program=program)
                    self._macros[program][name] = macro
                    success += 1

            # 카테고리 병합
            if "_categories" in data:
                for cat in data["_categories"]:
                    if cat not in self._categories:
                        self._categories.append(cat)

            self._notify_change("import", {"success": success, "skipped": skipped})
            return success, skipped

        except Exception as e:
            print(f"가져오기 오류: {e}")
            return 0, 0

    def import_from_vba_file(self, filepath: str, program: str, name: str = None) -> Optional[Macro]:
        """VBA 파일(.bas, .vba, .txt)에서 가져오기"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()

            if not name:
                name = Path(filepath).stem

            macro = Macro(
                name=name,
                code=code,
                program=program
            )

            if self.add(macro):
                return macro
            return None

        except Exception as e:
            print(f"VBA 파일 가져오기 오류: {e}")
            return None

    # Callbacks

    def on_change(self, callback: Callable):
        """변경 콜백 등록"""
        self._on_change_callbacks.append(callback)

    def _notify_change(self, action: str, data=None):
        """변경 알림"""
        for callback in self._on_change_callbacks:
            try:
                callback(action, data)
            except Exception:
                pass

    # Backup Management

    def get_backups(self) -> List[Tuple[str, datetime]]:
        """백업 파일 목록"""
        backups = []
        for f in BACKUPS_DIR.glob("macro_index_*.json"):
            try:
                # 파일명에서 시간 추출
                timestamp_str = f.stem.replace("macro_index_", "")
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                backups.append((str(f), timestamp))
            except ValueError:
                continue

        backups.sort(key=lambda x: x[1], reverse=True)
        return backups

    def restore_from_backup(self, backup_path: str) -> bool:
        """백업에서 복원"""
        try:
            # 현재 상태 백업
            self._create_backup()

            # 복원
            shutil.copy(backup_path, MACRO_INDEX_FILE)
            self.load()

            self._notify_change("restore_backup", backup_path)
            return True

        except Exception as e:
            print(f"백업 복원 오류: {e}")
            return False
