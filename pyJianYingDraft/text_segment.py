"""定义文本片段及其相关类"""

import uuid, json

from typing import Dict, List, Tuple, Any
from typing import Optional, Literal

from .time_util import Timerange
from .segment import Base_segment

class Text_style:
    """字体样式类"""

    size: float
    """字体大小"""

    bold: bool
    """是否加粗"""
    italic: bool
    """是否斜体"""
    underline: bool
    """是否加下划线"""

    color: Tuple[float, float, float]
    """字体颜色"""
    alpha: float
    """字体透明度"""

    align: Literal[0, 1, 2]
    """对齐方式"""
    vertical: bool
    """竖排文本"""

    def __init__(self, *, size: float = 15.0, bold: bool = False, italic: bool = False, underline: bool = False,
                 color: Tuple[float, float, float] = (1.0, 1.0, 1.0), alpha: float = 1.0,
                 align: Literal[0, 1, 2] = 0, vertical: bool = False):
        """
        Args:
            size (`float`): 字体大小
            bold (`bool`): 是否加粗
            italic (`bool`): 是否斜体
            underline (`bool`): 是否加下划线
            color (`Tuple[float, float, float]`): 字体颜色, RGB三元组, 取值范围[0, 1]
            alpha (`float`): 字体透明度, 取值范围[0, 1]
            align (`int`): 对齐方式, 0: 左对齐, 1: 居中, 2: 右对齐
            vertical (`bool`): 是否是竖排文本
        """
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline

        self.color = color
        self.alpha = alpha

        self.align = align
        self.vertical = vertical

class Text_segment(Base_segment):
    """文本片段类, 目前仅支持设置基本的字体样式"""

    text: str
    """文本内容"""
    style: Text_style
    """字体样式"""

    extra_material_refs: List[str]
    """附加的素材id列表, 用于链接动画/特效等"""

    def __init__(self, text: str, timerange: Timerange, style: Optional[Text_style] = None):
        super().__init__(uuid.uuid4().hex, timerange)

        self.text = text
        self.style = style or Text_style()

        self.extra_material_refs = []

    def export_material(self) -> Dict[str, Any]:
        """与此文本片段联系的素材, 以此不再单独定义Text_material类"""
        return {
            "add_type": 0,

            "typesetting": int(self.style.vertical),
            "alignment": self.style.align,

            # ?
            # "caption_template_info": {
            #     "category_id": "",
            #     "category_name": "",
            #     "effect_id": "",
            #     "is_new": False,
            #     "path": "",
            #     "request_id": "",
            #     "resource_id": "",
            #     "resource_name": "",
            #     "source_platform": 0
            # },

            # 混合 (+4)
            # "global_alpha": 1.0,

            # 描边 (+8)
            # "border_alpha": 1.0,
            # "border_color": "",
            # "border_width": 0.08,

            # 背景 (+16)
            # "background_style": 0,
            # "background_color": "",
            # "background_alpha": 1.0,
            # "background_round_radius": 0.0,
            # "background_height": 0.14,
            # "background_width": 0.14,
            # "background_horizontal_offset": 0.0,
            # "background_vertical_offset": 0.0,

            # 发光 (+64)，属性由extra_material_refs记录

            # 阴影 (+32)
            # "has_shadow": False,
            # "shadow_alpha": 0.9,
            # "shadow_angle": -45.0,
            # "shadow_color": "",
            # "shadow_distance": 5.0,
            # "shadow_point": {
            #     "x": 0.6363961030678928,
            #     "y": -0.6363961030678928
            # },
            # "shadow_smoothing": 0.45,

            # 整体字体设置, 似乎会被content覆盖
            # "font_category_id": "",
            # "font_category_name": "",
            # "font_id": "",
            # "font_name": "",
            # "font_path": "",
            # "font_resource_id": "",
            # "font_size": 15.0,
            # "font_source_platform": 0,
            # "font_team_id": "",
            # "font_title": "none",
            # "font_url": "",
            # "fonts": [],

            # 似乎会被content覆盖
            # "text_alpha": 1.0,
            # "text_color": "#FFFFFF",
            # "text_curve": None,
            # "text_preset_resource_id": "",
            # "text_size": 30,
            # "underline": False,


            "base_content": "",
            "bold_width": 0.0,

            "check_flag": 7,
            "combo_info": {
                "text_templates": []
            },
            "content": json.dumps({
                "styles": [
                    {
                        "fill": {
                            "alpha": 1.0,
                            "content": {
                                "render_type": "solid",
                                "solid": {
                                    "alpha": self.style.alpha,
                                    "color": list(self.style.color)
                                }
                            }
                        },
                        # "font": {
                        #     "id": "",
                        #     "path": "***.ttf"
                        # },
                        "range": [0, len(self.text)],
                        "size": self.style.size,
                        "bold": self.style.bold,
                        "italic": self.style.italic,
                        "underline": self.style.underline,
                    }
                ],
                "text": self.text
            }),
            "fixed_height": -1.0,
            "fixed_width": -1.0,
            "force_apply_line_max_width": False,

            "group_id": "",

            "id": self.material_id,
            "initial_scale": 1.0,
            "inner_padding": -1.0,
            "is_rich_text": False,
            "italic_degree": 0,
            "ktv_color": "",
            "language": "",
            "layer_weight": 1,
            "letter_spacing": 0.0,
            "line_feed": 1,
            "line_max_width": 0.82,
            "line_spacing": 0.02,
            "multi_language_current": "none",
            "name": "",
            "original_size": [],

            "preset_category": "",
            "preset_category_id": "",
            "preset_has_set_alignment": False,
            "preset_id": "",
            "preset_index": 0,
            "preset_name": "",

            "recognize_task_id": "",
            "recognize_type": 0,
            "relevance_segment": [],

            "shape_clip_x": False,
            "shape_clip_y": False,
            "source_from": "",
            "style_name": "",
            "sub_type": 0,
            "subtitle_keywords": None,
            "subtitle_template_original_fontsize": 0.0,
            "text_to_audio_ids": [],
            "tts_auto_update": False,
            "type": "text",

            "underline_offset": 0.22,
            "underline_width": 0.05,

            "use_effect_default_color": True,
            "words": {
                "end_time": [],
                "start_time": [],
                "text": []
            }
        }

    def export_json(self) -> Dict[str, Any]:
        ret = super().export_json()
        ret.update({
            # 与Video_segment一致的部分
            # "clip": {},
            # "hdr_settings": null,
            # "uniform_scale": {},

            # 与Media_segment一致的部分
            "source_timerange": None,
            "speed": 1.0,
            "volume": 1.0,
            "extra_material_refs": [self.extra_material_refs],
        })
        return ret