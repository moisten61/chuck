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

    def split_sections(self, markdown_text: str) -> List[str]:
        """
        根据所有级别的标题分割文本，并为每个部分添加其所属的层级标题
        
        Args:
            markdown_text: markdown格式的文本
            
        Returns:
            List[str]: 分割后的段落列表，每个段落包含其完整的标题层级
        """
        self.logger.info("开始按章节分割文本...")
        
        # 存储当前的标题层级（1-6级）
        current_titles = {level: None for level in range(1, self.max_level + 1)}
        
        sections = []
        current_section = []
        
        # 按行处理文本
        lines = markdown_text.split('\n')
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                if current_section:
                    current_section.append(line)
                continue
                
            # 检查是否是标题行（支持1-6级标题）
            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped_line)
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
            
            # 添加当前行到当前段落
            current_section.append(line)
        
        # 处理最后一个段落
        if current_section:
            section_text = self._build_section(current_titles, current_section)
            sections.append(section_text)
        
        # 添加分隔符
        formatted_sections = []
        for section in sections:
            formatted_sections.append(section + "\n\n" + "-" * 40 + "\n")
        
        self.logger.info(f"文本已分割为 {len(sections)} 个章节")
        return formatted_sections

    def _build_section(self, titles: Dict[int, str], content: List[str]) -> str:
        """
        构建包含完整标题层级的段落，只保留一次标题
        
        Args:
            titles: 当前的标题层级
            content: 段落内容
            
        Returns:
            str: 构建好的段落文本
        """
        # 找到当前段落的标题级别
        current_level = None
        for line in content:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                current_level = len(header_match.group(1))
                break
        
        if current_level is None:
            return "\n".join(content)
        
        # 收集所有相关的标题，但每个标题只出现一次
        section_titles = []
        seen_titles = set()  # 用于跟踪已经添加的标题内容
        
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
        
        # 组合标题和内容
        if section_titles:
            return "\n".join(section_titles + [""] + filtered_content)
        return "\n".join(filtered_content)

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