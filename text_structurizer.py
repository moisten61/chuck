from typing import List, Dict
from openai import AsyncOpenAI
import asyncio
import re
import logging
from tqdm import tqdm

class TextStructurizer:
    def __init__(self, api_key: str, chunk_size: int = 3000):
        """
        初始化文本结构化处理器
        
        Args:
            api_key: API密钥
            chunk_size: 每段文本的最大字符数（默认3000，约1000个汉字）
        """
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.bianxie.ai/v1"
        )
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)
        
    def split_text(self, text: str) -> List[str]:
        """
        将长文本分割成较小的块，每块最多1000个汉字
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分割后的文本块列表
        """
        # 如果文本长度在允许范围内，直接返回
        if len(text) <= self.chunk_size:
            return [text]
        
        # 按段落分割文本
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # 如果当前段落本身就超过了chunk_size，需要分割
            if len(para) > self.chunk_size:
                # 处理特长段落
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # 按句子分割特长段落
                sentences = re.split('(。|！|？)', para)
                temp_chunk = ""
                for i in range(0, len(sentences), 2):
                    sentence = sentences[i]
                    if i + 1 < len(sentences):
                        sentence += sentences[i + 1]
                    
                    if len(temp_chunk) + len(sentence) <= self.chunk_size:
                        temp_chunk += sentence
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = sentence
                
                if temp_chunk:
                    chunks.append(temp_chunk)
            else:
                # 处理普通段落
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk += (para + '\n\n')
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def split_by_sections(self, markdown_text: str) -> List[str]:
        """
        根据标题分割文本，并为每个部分添加其所属的层级标题（支持1-6级标题）
        
        Args:
            markdown_text: markdown格式的文本
            
        Returns:
            List[str]: 分割后的段落列表，每个段落包含其完整的标题层级
        """
        self.logger.info("开始按章节分割文本...")
        
        # 存储所有层级的标题（1-6级）
        current_titles = {
            1: None,  # 一级标题 #
            2: None,  # 二级标题 ##
            3: None,  # 三级标题 ###
            4: None,  # 四级标题 ####
            5: None,  # 五级标题 #####
            6: None   # 六级标题 ######
        }
        
        sections = []
        current_section = []
        lines = markdown_text.split('\n')
        
        for line in lines:
            if line.strip():  # 忽略空行
                # 检查是否是标题行（支持1-6级标题）
                header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                if header_match:
                    level = len(header_match.group(1))
                    title = line
                    
                    # 更新当前层级的标题
                    current_titles[level] = title
                    
                    # 如果已经有内容，保存当前段落
                    if current_section:
                        full_section = self._build_section_with_titles(current_titles, current_section)
                        sections.append(full_section)
                        current_section = []
                    
                    # 清除所有下级标题
                    for i in range(level + 1, 7):
                        current_titles[i] = None
                
                # 将当前行添加到当前段落
                current_section.append(line)
        
        # 处理最后一个段落
        if current_section:
            full_section = self._build_section_with_titles(current_titles, current_section)
            sections.append(full_section)
        
        # 添加分隔符
        formatted_sections = []
        for section in sections:
            formatted_sections.append(section + "\n\n" + "-" * 40 + "\n")
        
        self.logger.info(f"文本已分割为 {len(sections)} 个章节")
        return formatted_sections

    def _build_section_with_titles(self, current_titles: Dict[int, str], section_content: List[str]) -> str:
        """
        构建包含完整标题层级的段落
        """
        # 收集所有相关的标题
        relevant_titles = []
        for level in range(1, 7):  # 从1级到6级标题
            if current_titles[level]:
                relevant_titles.append(current_titles[level])
        
        # 组合标题和内容
        return "\n".join(relevant_titles + [""] + section_content)

    async def process_chunk(self, chunk: str, is_first: bool = False, previous_structure: str = None) -> str:
        """
        处理单个文本块，将其整理为带标题的结构化文本
        
        Args:
            chunk: 文本块
            is_first: 是否是第一个块
            previous_structure: 前一个块的结构（标题层级）
        """
        try:
            system_prompt = "你是一个专业的文档结构化助手，善于将文本整理为清晰的层级结构。"
            
            if is_first:
                self.logger.info("处理第一个文本块，创建文档结构...")
                prompt = f"""
                请将以下文本整理为结构化的格式，使用markdown标题：

                {chunk}

                要求：
                1. 分析文本内容，提取关键主题
                2. 创建合适的标题层级结构
                3. 使用markdown标题格式（#、##、###等）
                4. 不要修改原文任何内容
                5. 确保内容的逻辑性和连贯性
                """
            else:
                self.logger.info("处理后续文本块，保持结构一致...")
                prompt = f"""
                请接续前面的任务，继续整理文本格式，这是长文本的后续部分。前文的标题结构如下：

                {previous_structure}

                请处理以下内容，保持与前文结构一致：

                {chunk}

                要求：
                1. 参考前文的标题结构
                2. 保持标题层级的一致性
                3. 使用markdown标题格式
                4. 不要修改原文任何内容
                5. 确保与前文的连贯性
                """

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"处理文本块时发生错误: {str(e)}")
            raise

    def extract_structure(self, text: str) -> str:
        """
        提取文本中的标题结构
        """
        structure = []
        for line in text.split('\n'):
            if line.strip().startswith('#'):
                structure.append(line.strip())
        return '\n'.join(structure)

    async def process_text(self, input_text: str) -> str:
        """
        处理输入文本，生成结构化内容
        """
        try:
            self.logger.info("开始处理文本...")
            chunks = self.split_text(input_text)
            self.logger.info(f"文本已分割为 {len(chunks)} 个块")
            
            results = []
            previous_structure = None
            
            # 使用tqdm创建进度条
            for i in tqdm(range(len(chunks)), desc="处理文本块"):
                chunk = chunks[i]
                result = await self.process_chunk(
                    chunk, 
                    is_first=(i == 0),
                    previous_structure=previous_structure
                )
                results.append(result)
                # 更新前文结构
                previous_structure = self.extract_structure(result)
                
            if len(results) == 1:
                self.logger.info("文本处理完成")
                return results[0]
            
            self.logger.info("合并处理结果...")
            final_result = await self.merge_results(results)
            self.logger.info("文本处理完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"处理文本时发生错误: {str(e)}")
            raise

    async def merge_results(self, results: List[str]) -> str:
        """
        合并多个处理结果
        """
        try:
            self.logger.info("开始合并处理结果...")
            
            # 使用第一个结果作为基础
            merged_text = results[0]
            structure = self.extract_structure(merged_text)
            
            # 记录已有的标题，避免重复
            existing_titles = set(structure.split('\n'))
            
            # 合并后续结果
            for result in results[1:]:
                lines = result.split('\n')
                content_lines = []
                current_title = None
                
                for line in lines:
                    stripped_line = line.strip()
                    # 处理标题行
                    if stripped_line.startswith('#'):
                        if stripped_line not in existing_titles:
                            current_title = stripped_line
                            content_lines.append(line)
                            existing_titles.add(stripped_line)
                    # 处理内容行
                    else:
                        # 只添加非空行和有意义的内容
                        if stripped_line and not stripped_line.isspace():
                            content_lines.append(line)
                
                # 添加新内容，确保有适当的分隔
                if content_lines:
                    if not merged_text.endswith('\n'):
                        merged_text += '\n'
                    if not merged_text.endswith('\n\n'):
                        merged_text += '\n'
                    merged_text += '\n'.join(content_lines)
            
            self.logger.info("文本合并完成")
            return merged_text
            
        except Exception as e:
            self.logger.error(f"合并结果时发生错误: {str(e)}")
            raise