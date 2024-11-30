from text_structurizer import TextStructurizer
from section_splitter import SectionSplitter
import os
from dotenv import load_dotenv
import asyncio
import logging
import sys

def setup_logging():
    """
    配置日志系统
    """
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler('text_structurizer.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

async def main():
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 加载环境变量
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("未找到API密钥")
            return
        
        # 初始化处理器
        structurizer = TextStructurizer(api_key)
        splitter = SectionSplitter()
        
        # 获取用户输入
        logger.info("等待用户输入文本...")
        print("请输入需要处理的文本（输入'END'结束）：")
        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)
        
        input_text = '\n'.join(lines)
        
        if not input_text.strip():
            logger.warning("输入文本为空")
            return
        
        # 询问用户是否需要文本整理
        need_structuring = input("是否需要先进行文本整理？(y/n): ").lower() == 'y'
        
        # 步骤A：文本整理（可选）
        if need_structuring:
            logger.info("开始文本整理...")
            input_text = await structurizer.process_text(input_text)
            print("\n整理后的文本：")
            print(input_text)
            print("\n" + "="*50 + "\n")
        
        # 步骤B：章节分割
        logger.info("开始章节分割...")
        sections = splitter.split_sections(input_text)
        
        print("\n分割后的章节：")
        for section in sections:
            # 直接输出章节内容，不显示标题层级信息
            print("\n" + section)
        
        logger.info("处理完成")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        print(f"处理过程中出现错误：{str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 