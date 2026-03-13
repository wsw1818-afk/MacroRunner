"""
PowerPoint 매크로 직접 실행기
VBA 대신 Python으로 직접 PPT를 조작
"""
from typing import Tuple, Optional
import pythoncom
import win32com.client


class PPTMacroExecutor:
    """PowerPoint 매크로를 Python으로 직접 실행"""

    # mso 상수
    MSO_PICTURE = 13
    MSO_PLACEHOLDER = 14
    MSO_FALSE = 0
    MSO_TRUE = -1
    MSO_BRING_TO_FRONT = 0

    def __init__(self):
        self.ppt_app = None

    def _get_ppt_app(self):
        """PowerPoint 앱 객체 가져오기"""
        pythoncom.CoInitialize()
        return win32com.client.GetActiveObject("PowerPoint.Application")

    def execute_image_placement(self, mode: int = 1, margin: float = 0, doc_index: int = None) -> Tuple[bool, str]:
        """
        이미지 자동 배치 실행

        Args:
            mode: 1=비율무시, 2=비율유지, 3=여백맞춤
            margin: 여백 (mode=3일 때 사용)
            doc_index: 선택된 문서 인덱스 (None이면 활성 문서 사용)

        Returns:
            (성공여부, 메시지)
        """
        try:
            ppt_app = self._get_ppt_app()

            if ppt_app.Presentations.Count == 0:
                return False, "활성 프레젠테이션이 없습니다."

            # 선택된 문서 또는 활성 문서 가져오기
            if doc_index and doc_index <= ppt_app.Presentations.Count:
                presentation = ppt_app.Presentations(doc_index)
                # 해당 프레젠테이션의 윈도우 활성화
                if presentation.Windows.Count > 0:
                    presentation.Windows(1).Activate()
            else:
                presentation = ppt_app.ActivePresentation

            # 현재 슬라이드 가져오기
            try:
                slide = ppt_app.ActiveWindow.View.Slide
            except:
                return False, "활성화된 슬라이드가 없습니다."

            processed_count = 0
            OVERLAP_THRESHOLD = 0.05  # 5%만 겹쳐도 배치 (살짝 닿아도 동작)

            # 이미지 목록 먼저 수집 (역순으로)
            images = []
            for i in range(slide.Shapes.Count, 0, -1):
                shp = slide.Shapes(i)
                if shp.Type == self.MSO_PICTURE:
                    images.append(shp)

            # 각 이미지 처리
            for img in images:
                # 가장 많이 겹치는 대상 찾기
                best_cell = self._find_best_target(slide, img, OVERLAP_THRESHOLD)

                if best_cell:
                    # 이미지 배치
                    self._place_image(img, best_cell, mode, margin)
                    # 맨 앞으로 가져오기
                    img.ZOrder(self.MSO_BRING_TO_FRONT)
                    processed_count += 1

            if processed_count > 0:
                return True, f"현재 슬라이드 이미지 {processed_count}개 배치 완료!"
            else:
                return True, "배치할 이미지가 없거나 대상 도형을 찾지 못했습니다."

        except Exception as e:
            return False, f"PPT 매크로 실행 실패: {e}"

    def _find_best_target(self, slide, img, threshold: float) -> Optional[dict]:
        """이미지와 가장 많이 겹치는 대상 찾기"""
        best_area = 0
        best_cell = None

        for shp in slide.Shapes:
            if shp.Name == img.Name:
                continue

            if shp.HasTable:
                # 테이블인 경우 각 셀 검사
                tbl = shp.Table
                tbl_left = shp.Left
                tbl_top = shp.Top

                cell_top = tbl_top
                for r in range(1, tbl.Rows.Count + 1):
                    cell_left = tbl_left
                    cell_h = tbl.Rows(r).Height

                    for c in range(1, tbl.Columns.Count + 1):
                        cell_w = tbl.Columns(c).Width

                        # 겹침 면적 계산
                        area = self._calculate_overlap(
                            img, cell_left, cell_top, cell_w, cell_h
                        )

                        cand_area = cell_w * cell_h
                        ratio = area / cand_area if cand_area > 0 else 0

                        if ratio >= threshold and area > best_area:
                            best_area = area
                            best_cell = {
                                'left': cell_left,
                                'top': cell_top,
                                'width': cell_w,
                                'height': cell_h
                            }

                        cell_left += cell_w
                    cell_top += cell_h

            elif shp.Type != self.MSO_PICTURE and shp.Type != self.MSO_PLACEHOLDER:
                # 일반 도형
                area = self._calculate_overlap(
                    img, shp.Left, shp.Top, shp.Width, shp.Height
                )

                cand_area = shp.Width * shp.Height
                ratio = area / cand_area if cand_area > 0 else 0

                if ratio >= threshold and area > best_area:
                    best_area = area
                    best_cell = {
                        'left': shp.Left,
                        'top': shp.Top,
                        'width': shp.Width,
                        'height': shp.Height
                    }

        return best_cell

    def _calculate_overlap(self, img, target_left, target_top, target_width, target_height) -> float:
        """겹침 면적 계산"""
        img_right = img.Left + img.Width
        img_bottom = img.Top + img.Height
        tgt_right = target_left + target_width
        tgt_bottom = target_top + target_height

        # 겹치는 영역
        l = max(img.Left, target_left)
        t = max(img.Top, target_top)
        r = min(img_right, tgt_right)
        b = min(img_bottom, tgt_bottom)

        if r > l and b > t:
            return (r - l) * (b - t)
        return 0

    def _place_image(self, img, target: dict, mode: int, margin: float):
        """이미지를 대상 영역에 배치"""
        tl = target['left']
        tt = target['top']
        tw = target['width']
        th = target['height']

        # 여백 적용
        if margin > 0:
            tw = tw - 2 * margin
            th = th - 2 * margin
            tl = tl + margin
            tt = tt + margin
            if tw <= 0 or th <= 0:
                return

        if mode == 1:
            # 비율 무시 채우기
            img.LockAspectRatio = self.MSO_FALSE
            img.Width = tw
            img.Height = th
            img.Left = tl
            img.Top = tt

        elif mode == 2:
            # 비율 유지 채우기
            img.LockAspectRatio = self.MSO_TRUE
            img_ratio = img.Width / img.Height
            tgt_ratio = tw / th

            if img_ratio > tgt_ratio:
                img.Height = th
            else:
                img.Width = tw

            img.Left = tl + (tw - img.Width) / 2
            img.Top = tt + (th - img.Height) / 2

        elif mode == 3:
            # 여백 후 채우기
            img.LockAspectRatio = self.MSO_FALSE
            img.Width = tw
            img.Height = th
            img.Left = tl
            img.Top = tt


# 전역 인스턴스
ppt_executor = PPTMacroExecutor()
