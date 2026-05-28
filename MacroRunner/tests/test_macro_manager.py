"""
MacroManager 테스트
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.macro_manager import MacroManager, Macro


class TestMacro:
    """Macro 데이터 클래스 테스트"""

    def test_create_macro(self):
        """매크로 생성 테스트"""
        macro = Macro(
            name="테스트매크로",
            code="Sub Test()\nEnd Sub",
            program="excel"
        )

        assert macro.name == "테스트매크로"
        assert macro.code == "Sub Test()\nEnd Sub"
        assert macro.program == "excel"
        assert macro.category == "일반"
        assert macro.favorite == False
        assert macro.use_count == 0

    def test_macro_to_dict(self):
        """매크로 딕셔너리 변환 테스트"""
        macro = Macro(
            name="테스트",
            code="Sub X()\nEnd Sub",
            program="ppt",
            description="설명",
            category="보고서",
            favorite=True
        )

        data = macro.to_dict()

        assert data["name"] == "테스트"
        assert data["code"] == "Sub X()\nEnd Sub"
        assert data["program"] == "ppt"
        assert data["description"] == "설명"
        assert data["category"] == "보고서"
        assert data["favorite"] == True

    def test_macro_from_dict(self):
        """딕셔너리에서 매크로 생성 테스트"""
        data = {
            "code": "Sub Y()\nEnd Sub",
            "description": "테스트 설명"
        }

        macro = Macro.from_dict(data, name="테스트2", program="word")

        assert macro.name == "테스트2"
        assert macro.program == "word"
        assert macro.code == "Sub Y()\nEnd Sub"
        assert macro.description == "테스트 설명"

    def test_macro_from_dict_legacy(self):
        """이전 버전 형식 호환성 테스트"""
        # 이전 버전 형식 (category, favorite 없음)
        data = {
            "code": "Sub Old()\nEnd Sub",
            "created": "2024-01-01T00:00:00",
            "modified": "2024-01-01T00:00:00"
        }

        macro = Macro.from_dict(data, name="레거시", program="excel")

        assert macro.category == "일반"
        assert macro.favorite == False
        assert macro.use_count == 0


class TestMacroManager:
    """MacroManager 테스트"""

    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def manager(self, temp_dir, monkeypatch):
        """테스트용 MacroManager"""
        # 경로 패치
        monkeypatch.setattr("src.core.macro_manager.MACROS_DIR", temp_dir / "macros")
        monkeypatch.setattr("src.core.macro_manager.BACKUPS_DIR", temp_dir / "backups")
        monkeypatch.setattr("src.core.macro_manager.MACRO_INDEX_FILE", temp_dir / "macros" / "macro_index.json")

        return MacroManager()

    def test_add_macro(self, manager):
        """매크로 추가 테스트"""
        macro = Macro(
            name="새매크로",
            code="Sub New()\nEnd Sub",
            program="excel"
        )

        result = manager.add(macro)
        assert result == True

        # 중복 추가 시도
        result = manager.add(macro)
        assert result == False

    def test_get_macro(self, manager):
        """매크로 조회 테스트"""
        macro = Macro(name="조회테스트", code="Sub Get()\nEnd Sub", program="ppt")
        manager.add(macro)

        result = manager.get("ppt", "조회테스트")
        assert result is not None
        assert result.name == "조회테스트"

        # 없는 매크로
        result = manager.get("ppt", "없는매크로")
        assert result is None

    def test_update_macro(self, manager):
        """매크로 업데이트 테스트"""
        macro = Macro(name="업데이트", code="Sub Old()\nEnd Sub", program="excel")
        manager.add(macro)

        # 업데이트 (새 객체로)
        macro2 = Macro(name="업데이트", code="Sub New()\nEnd Sub", program="excel")
        result = manager.update(macro2)
        assert result == True

        # 버전 확인
        updated = manager.get("excel", "업데이트")
        assert updated.version == 2
        assert len(updated.history) == 1

    def test_delete_macro(self, manager):
        """매크로 삭제 테스트"""
        macro = Macro(name="삭제대상", code="Sub Del()\nEnd Sub", program="word")
        manager.add(macro)

        result = manager.delete("word", "삭제대상")
        assert result == True

        # 확인
        assert manager.get("word", "삭제대상") is None

    def test_rename_macro(self, manager):
        """매크로 이름 변경 테스트"""
        macro = Macro(name="원래이름", code="Sub Ren()\nEnd Sub", program="excel")
        manager.add(macro)

        result = manager.rename("excel", "원래이름", "새이름")
        assert result == True

        assert manager.get("excel", "원래이름") is None
        assert manager.get("excel", "새이름") is not None

    def test_duplicate_macro(self, manager):
        """매크로 복제 테스트"""
        macro = Macro(name="원본", code="Sub Orig()\nEnd Sub", program="ppt")
        manager.add(macro)

        duplicate = manager.duplicate("ppt", "원본")
        assert duplicate is not None
        assert duplicate.name == "원본 (복사본)"
        assert duplicate.code == macro.code

    def test_search(self, manager):
        """검색 테스트"""
        manager.add(Macro(name="엑셀보고서", code="Sub Report()\nEnd Sub", program="excel"))
        manager.add(Macro(name="PPT자료", code="Sub Ppt()\nEnd Sub", program="ppt"))
        manager.add(Macro(name="엑셀차트", code="Sub Chart()\nEnd Sub", program="excel"))

        # 이름 검색
        results = manager.search("엑셀")
        assert len(results) == 2

        # 프로그램 필터
        results = manager.search("엑셀", "excel")
        assert len(results) == 2

        # 코드 검색
        results = manager.search("Report")
        assert len(results) == 1

    def test_favorites(self, manager):
        """즐겨찾기 테스트"""
        macro = Macro(name="즐겨찾기", code="Sub Fav()\nEnd Sub", program="excel")
        manager.add(macro)

        # 토글
        result = manager.toggle_favorite("excel", "즐겨찾기")
        assert result == True

        # 확인
        favorites = manager.get_favorites("excel")
        assert len(favorites) == 1

    def test_categories(self, manager):
        """카테고리 테스트"""
        # 기본 카테고리 확인
        categories = manager.get_categories()
        assert "일반" in categories

        # 카테고리 추가
        manager.add_category("커스텀")
        assert "커스텀" in manager.get_categories()

        # 카테고리별 필터
        macro = Macro(name="카테고리테스트", code="Sub Cat()\nEnd Sub", program="excel", category="커스텀")
        manager.add(macro)

        results = manager.filter_by_category("커스텀")
        assert len(results) == 1

    def test_save_and_load(self, manager, temp_dir):
        """저장 및 로드 테스트"""
        # 매크로 추가
        macro = Macro(name="저장테스트", code="Sub Save()\nEnd Sub", program="excel")
        manager.add(macro)
        manager.save()

        # 새 매니저로 로드
        from src.core.macro_manager import MacroManager
        new_manager = MacroManager()

        result = new_manager.get("excel", "저장테스트")
        assert result is not None
        assert result.code == "Sub Save()\nEnd Sub"

    def test_frozen_syncs_newer_packaged_macro(self, temp_dir, monkeypatch):
        """EXE default macro updates refresh the user copy."""
        from src.core import macro_manager as macro_manager_module

        package_macros = temp_dir / "package" / "macros"
        user_macros = temp_dir / "user" / "macros"
        package_macros.mkdir(parents=True)
        user_macros.mkdir(parents=True)

        package_data = {
            "_categories": ["General", "Automation"],
            "excel": {
                "BuiltIn": {
                    "name": "BuiltIn",
                    "code": "Sub NewCode()\nEnd Sub",
                    "program": "excel",
                    "description": "new",
                    "category": "Automation",
                    "version": 3,
                    "modified": "2026-05-25T00:00:00",
                    "history": []
                }
            },
            "ppt": {},
            "word": {}
        }
        user_data = {
            "_categories": ["General"],
            "excel": {
                "BuiltIn": {
                    "name": "BuiltIn",
                    "code": "Sub OldCode()\nEnd Sub",
                    "program": "excel",
                    "description": "old",
                    "category": "General",
                    "favorite": True,
                    "use_count": 7,
                    "last_used": "2026-05-24T12:00:00",
                    "version": 2,
                    "modified": "2026-01-01T00:00:00",
                    "history": []
                }
            },
            "ppt": {},
            "word": {}
        }

        (package_macros / "macro_index.json").write_text(
            json.dumps(package_data), encoding="utf-8"
        )
        (user_macros / "macro_index.json").write_text(
            json.dumps(user_data), encoding="utf-8"
        )

        monkeypatch.setattr(macro_manager_module, "IS_FROZEN", True)
        monkeypatch.setattr(macro_manager_module, "PACKAGE_MACROS_DIR", package_macros)
        monkeypatch.setattr(macro_manager_module, "MACROS_DIR", user_macros)
        monkeypatch.setattr(macro_manager_module, "BACKUPS_DIR", temp_dir / "backups")
        monkeypatch.setattr(
            macro_manager_module,
            "MACRO_INDEX_FILE",
            user_macros / "macro_index.json"
        )

        frozen_manager = MacroManager()
        macro = frozen_manager.get("excel", "BuiltIn")

        assert macro.code == "Sub NewCode()\nEnd Sub"
        assert macro.favorite is True
        assert macro.use_count == 7
        assert macro.last_used == "2026-05-24T12:00:00"
        assert "Automation" in frozen_manager.get_categories()
        assert any("OldCode" in item["code"] for item in macro.history)

    def test_frozen_sync_uses_higher_packaged_version(self, temp_dir, monkeypatch):
        """Packaged default macro updates win when their version is higher."""
        from src.core import macro_manager as macro_manager_module

        package_macros = temp_dir / "package" / "macros"
        user_macros = temp_dir / "user" / "macros"
        package_macros.mkdir(parents=True)
        user_macros.mkdir(parents=True)

        package_data = {
            "_categories": ["General"],
            "excel": {
                "BuiltIn": {
                    "name": "BuiltIn",
                    "code": "Sub PackageCode()\nEnd Sub",
                    "program": "excel",
                    "version": 3,
                    "modified": "2026-05-25T00:00:00"
                }
            },
            "ppt": {},
            "word": {}
        }
        user_data = {
            "_categories": ["General"],
            "excel": {
                "BuiltIn": {
                    "name": "BuiltIn",
                    "code": "Sub UserCode()\nEnd Sub",
                    "program": "excel",
                    "version": 2,
                    "modified": "2026-06-01T00:00:00"
                }
            },
            "ppt": {},
            "word": {}
        }

        (package_macros / "macro_index.json").write_text(
            json.dumps(package_data), encoding="utf-8"
        )
        (user_macros / "macro_index.json").write_text(
            json.dumps(user_data), encoding="utf-8"
        )

        monkeypatch.setattr(macro_manager_module, "IS_FROZEN", True)
        monkeypatch.setattr(macro_manager_module, "PACKAGE_MACROS_DIR", package_macros)
        monkeypatch.setattr(macro_manager_module, "MACROS_DIR", user_macros)
        monkeypatch.setattr(macro_manager_module, "BACKUPS_DIR", temp_dir / "backups")
        monkeypatch.setattr(
            macro_manager_module,
            "MACRO_INDEX_FILE",
            user_macros / "macro_index.json"
        )

        frozen_manager = MacroManager()

        assert frozen_manager.get("excel", "BuiltIn").code == "Sub PackageCode()\nEnd Sub"

    def test_frozen_sync_keeps_newer_user_macro_at_same_version(self, temp_dir, monkeypatch):
        """User-edited macros newer than the package are preserved when versions match."""
        from src.core import macro_manager as macro_manager_module

        package_macros = temp_dir / "package" / "macros"
        user_macros = temp_dir / "user" / "macros"
        package_macros.mkdir(parents=True)
        user_macros.mkdir(parents=True)

        package_data = {
            "_categories": ["General"],
            "excel": {
                "BuiltIn": {
                    "name": "BuiltIn",
                    "code": "Sub PackageCode()\nEnd Sub",
                    "program": "excel",
                    "version": 2,
                    "modified": "2026-05-25T00:00:00"
                }
            },
            "ppt": {},
            "word": {}
        }
        user_data = {
            "_categories": ["General"],
            "excel": {
                "BuiltIn": {
                    "name": "BuiltIn",
                    "code": "Sub UserCode()\nEnd Sub",
                    "program": "excel",
                    "version": 2,
                    "modified": "2026-06-01T00:00:00"
                }
            },
            "ppt": {},
            "word": {}
        }

        (package_macros / "macro_index.json").write_text(
            json.dumps(package_data), encoding="utf-8"
        )
        (user_macros / "macro_index.json").write_text(
            json.dumps(user_data), encoding="utf-8"
        )

        monkeypatch.setattr(macro_manager_module, "IS_FROZEN", True)
        monkeypatch.setattr(macro_manager_module, "PACKAGE_MACROS_DIR", package_macros)
        monkeypatch.setattr(macro_manager_module, "MACROS_DIR", user_macros)
        monkeypatch.setattr(macro_manager_module, "BACKUPS_DIR", temp_dir / "backups")
        monkeypatch.setattr(
            macro_manager_module,
            "MACRO_INDEX_FILE",
            user_macros / "macro_index.json"
        )

        frozen_manager = MacroManager()

        assert frozen_manager.get("excel", "BuiltIn").code == "Sub UserCode()\nEnd Sub"

    def test_packaged_excel_macro_has_debug_logging(self):
        """The packaged Excel placement macro includes target-selection diagnostics."""
        index_path = Path(__file__).parent.parent / "macros" / "macro_index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        macro = next(iter(data["excel"].values()))

        assert macro["version"] >= 7
        assert "MR_RectGapDistance" in macro["code"]
        assert "MR_LogDebug" in macro["code"]
        assert "MacroRunner_excel_debug.log" in macro["code"]
        assert "MR_FitPictures_Fill_WithMargin" in macro["code"]
        assert "MR_AskMarginPoints" in macro["code"]
        assert "MR_TargetWithMargin" in macro["code"]

    def test_packaged_excel_fill_sets_position_after_size(self):
        """Excel can shift pictures while resizing, so fill mode positions last."""
        index_path = Path(__file__).parent.parent / "macros" / "macro_index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        code = next(iter(data["excel"].values()))["code"]
        fill_body = code.split("Private Sub MR_PlaceFill", 1)[1].split("End Sub", 1)[0]

        assert fill_body.index(".Width = target.Width") < fill_body.index(".Left = target.Left")
        assert fill_body.index(".Height = target.Height") < fill_body.index(".Top = target.Top")

    def test_packaged_excel_margin_shrinks_target_before_placement(self):
        """Margin mode places pictures inside an inset target rectangle."""
        index_path = Path(__file__).parent.parent / "macros" / "macro_index.json"
        data = json.loads(index_path.read_text(encoding="utf-8"))
        code = next(iter(data["excel"].values()))["code"]
        margin_body = code.split("Private Function MR_TargetWithMargin", 1)[1].split("End Function", 1)[0]

        assert "result.Left = source.Left + marginPoints" in margin_body
        assert "result.Top = source.Top + marginPoints" in margin_body
        assert "result.Width = source.Width - (marginPoints * 2)" in margin_body
        assert "result.Height = source.Height - (marginPoints * 2)" in margin_body

    def test_export_import(self, manager, temp_dir):
        """내보내기/가져오기 테스트"""
        # 매크로 추가
        manager.add(Macro(name="내보내기1", code="Sub E1()\nEnd Sub", program="excel"))
        manager.add(Macro(name="내보내기2", code="Sub E2()\nEnd Sub", program="ppt"))

        # 내보내기
        export_path = str(temp_dir / "export.json")
        result = manager.export_macros(export_path)
        assert result == True

        # 파일 확인
        assert Path(export_path).exists()

        # 가져오기 (새 매니저)
        from src.core.macro_manager import MacroManager

        # 기존 매크로 삭제
        manager.delete("excel", "내보내기1")
        manager.delete("ppt", "내보내기2")

        success, skipped = manager.import_macros(export_path)
        assert success == 2
        assert skipped == 0

    def test_version_history(self, manager):
        """버전 히스토리 테스트"""
        # 버전 1 추가
        macro1 = Macro(name="버전테스트", code="Sub V1()\nEnd Sub", program="excel")
        manager.add(macro1)

        # 버전 2로 업데이트 (새 객체 생성)
        macro2 = Macro(name="버전테스트", code="Sub V2()\nEnd Sub", program="excel")
        manager.update(macro2)

        # 버전 3으로 업데이트 (새 객체 생성)
        macro3 = Macro(name="버전테스트", code="Sub V3()\nEnd Sub", program="excel")
        manager.update(macro3)

        # 히스토리 확인 (V1, V2가 히스토리에 저장됨)
        history = manager.get_history("excel", "버전테스트")
        assert len(history) == 2

        # 히스토리에 V1 코드가 있는지 확인
        assert any("V1" in h["code"] for h in history)
        assert any("V2" in h["code"] for h in history)

        # 현재 코드는 V3
        current = manager.get("excel", "버전테스트")
        assert "V3" in current.code

        # 버전 1로 복원 (V1 코드)
        result = manager.restore_version("excel", "버전테스트", 1)
        assert result == True

        restored = manager.get("excel", "버전테스트")
        assert "V1" in restored.code

    def test_usage_tracking(self, manager):
        """사용량 추적 테스트"""
        macro = Macro(name="사용량", code="Sub Use()\nEnd Sub", program="excel")
        manager.add(macro)

        # 사용 기록
        manager.record_usage("excel", "사용량")
        manager.record_usage("excel", "사용량")
        manager.record_usage("excel", "사용량")

        result = manager.get("excel", "사용량")
        assert result.use_count == 3
        assert result.last_used is not None


class TestMacroManagerEdgeCases:
    """엣지 케이스 테스트"""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def manager(self, temp_dir, monkeypatch):
        monkeypatch.setattr("src.core.macro_manager.MACROS_DIR", temp_dir / "macros")
        monkeypatch.setattr("src.core.macro_manager.BACKUPS_DIR", temp_dir / "backups")
        monkeypatch.setattr("src.core.macro_manager.MACRO_INDEX_FILE", temp_dir / "macros" / "macro_index.json")
        return MacroManager()

    def test_empty_name(self, manager):
        """빈 이름 처리"""
        macro = Macro(name="", code="Sub Empty()\nEnd Sub", program="excel")
        result = manager.add(macro)
        # 빈 이름도 키로 사용 가능 (실제로는 UI에서 방지)
        assert result == True

    def test_special_characters_in_name(self, manager):
        """특수 문자가 포함된 이름"""
        macro = Macro(
            name="매크로 (테스트) - 버전1.0",
            code="Sub Special()\nEnd Sub",
            program="excel"
        )
        result = manager.add(macro)
        assert result == True

        retrieved = manager.get("excel", "매크로 (테스트) - 버전1.0")
        assert retrieved is not None

    def test_very_long_code(self, manager):
        """매우 긴 코드"""
        long_code = "Sub Long()\n" + ("    MsgBox 1\n" * 1000) + "End Sub"
        macro = Macro(name="긴코드", code=long_code, program="excel")

        manager.add(macro)
        manager.save()

        retrieved = manager.get("excel", "긴코드")
        assert len(retrieved.code) == len(long_code)

    def test_unicode_in_code(self, manager):
        """유니코드가 포함된 코드"""
        code = '''Sub 한글매크로()
    MsgBox "안녕하세요! 👋"
    ' 주석: 日本語テスト
End Sub'''
        macro = Macro(name="유니코드", code=code, program="excel")

        manager.add(macro)
        manager.save()

        retrieved = manager.get("excel", "유니코드")
        assert "안녕하세요" in retrieved.code
        assert "👋" in retrieved.code

    def test_concurrent_operations(self, manager):
        """동시 작업 시뮬레이션"""
        import threading

        def add_macro(name):
            macro = Macro(name=name, code=f"Sub {name}()\nEnd Sub", program="excel")
            manager.add(macro)

        threads = []
        for i in range(10):
            t = threading.Thread(target=add_macro, args=(f"동시{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 모든 매크로 추가 확인
        all_macros = manager.get_all("excel")
        assert len(all_macros) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
