from typing import List, Dict
import re
import logging

class SectionSplitter:
    def __init__(self):
        """
        初始化章节分割器
        """
        self.logger = logging.getLogger(__name__)
        # 支持6级标题
        self.max_level = 6
        # 定义目录相关的关键词
        self.toc_keywords = {'目录', 'contents', 'table of contents', 'toc'}

    def split_sections(self, markdown_text: str) -> List[str]:
        """
        根据标题分割文本，并为每个部分添加其所属的层级标题
        """
        self.logger.info("开始按章节分割文本...")
        
        # 第一步：按标题分割文本
        sections = self._split_by_headers(markdown_text)
        
        # 第二步：过滤掉不需要的段落
        filtered_sections = self._filter_sections(sections)
        
        self.logger.info(f"文本已分割为 {len(filtered_sections)} 个章节")
        return filtered_sections

    def _split_by_headers(self, markdown_text: str) -> List[str]:
        """
        第一步：按标题进行初始分割
        """
        current_titles = {level: None for level in range(1, self.max_level + 1)}
        sections = []
        current_section = []
        
        lines = markdown_text.split('\n')
        for line in lines:
            if line.strip():  # 忽略空行
                # 检查是否是标题行
                header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                if header_match:
                    level = len(header_match.group(1))
                    
                    # 如果已经有内容，保存当前段落
                    if current_section:
                        section_text = self._build_section(current_titles, current_section)
                        sections.append(section_text)
                        current_section = []
                    
                    # 更新当前层级的标题
                    current_titles[level] = line
                    # 清除所有下级标题
                    for i in range(level + 1, self.max_level + 1):
                        current_titles[i] = None
                
                # 将当前行添加到当前段落
                current_section.append(line)
        
        # 处理最后一个段落
        if current_section:
            section_text = self._build_section(current_titles, current_section)
            sections.append(section_text)
            
        return sections

    def _filter_sections(self, sections: List[str]) -> List[str]:
        """
        第二步：过滤掉不需要的段落
        - 只有标题没有内容的段落
        - 目录段落
        """
        filtered_sections = []
        
        for section in sections:
            # 跳过空段落
            if not section.strip():
                continue
                
            # 跳过目录段落
            if self._is_toc_section(section):
                continue
                
            # 检查是否只有标题
            if not self._has_actual_content(section):
                continue
                
            # 添加分隔符
            filtered_sections.append(section + "\n\n" + "-" * 40 + "\n")
            
        return filtered_sections

    def _has_actual_content(self, section: str) -> bool:
        """
        检查段落是否包含实际内容（不仅仅是标题）
        """
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^#{1,6}\s+', line):
                return True
        return False

    def _is_toc_section(self, section: str) -> bool:
        """
        检查是否是目录段落
        """
        lines = section.split('\n')
        # 检查最后一个标题是否包含目录关键词
        last_title = None
        for line in lines:
            if re.match(r'^#{1,6}\s+(.+)$', line.strip()):
                last_title = line.strip().split()[-1].lower()
        
        # 检查内容是否符合目录特征
        has_numbering = False
        has_bullet_points = False
        content_lines = [line.strip() for line in lines if line.strip() 
                        and not re.match(r'^#{1,6}\s+', line.strip())]
        
        for line in content_lines:
            if re.match(r'^\d+\.', line) or re.match(r'^[一二三四五六七八九十]+、', line):
                has_numbering = True
            if line.startswith('-') or line.startswith('*') or re.match(r'^\d+\)', line):
                has_bullet_points = True
        
        # 如果最后一个标题是"目录"相关，或者内容具有目录特征，则认为是目录段落
        return (last_title in self.toc_keywords or 
                (has_numbering and has_bullet_points and len(content_lines) > 3))

    def _build_section(self, titles: Dict[int, str], content: List[str]) -> str:
        """
        构建包含完整标题层级的段落，只保留有内容的段落
        """
        # 检查是否有实际内容（不仅仅是标题）
        has_content = False
        for line in content:
            if line.strip() and not re.match(r'^#{1,6}\s+', line.strip()):
                has_content = True
                break
        
        if not has_content:
            return ""
        
        # 收集所有相关的标题
        section_titles = []
        seen_titles = set()
        
        # 找到当前段落的标题级别
        current_level = None
        for line in content:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                current_level = len(header_match.group(1))
                break
        
        if current_level:
            # 只添加当前标题级别之前的标题
            for level in range(1, current_level + 1):
                if titles[level] and titles[level].strip() not in seen_titles:
                    section_titles.append(titles[level])
                    seen_titles.add(titles[level].strip())
        
        # 从原始内容中移除重复的标题
        filtered_content = []
        for line in content:
            if not line.strip() in seen_titles:
                filtered_content.append(line)
        
        # 构建段落文本
        section_text = "\n".join(section_titles + [""] + filtered_content) if section_titles else "\n".join(filtered_content)
        
        # 如果是目录段落，返回空字符串
        if self._is_toc_section(section_text):
            return ""
            
        return section_text

    def get_section_info(self, section: str) -> Dict[str, str]:
        """
        获取段落的标题信息
        
        Args:
            section: 段落文本
            
        Returns:
            Dict[str, str]: 包含各级标题的字典
        """
        titles = {f"level{i}": None for i in range(1, self.max_level + 1)}
        
        lines = section.split('\n')
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                level = len(header_match.group(1))
                titles[f"level{level}"] = header_match.group(2)
                
        return titles 