import os
import re
import datetime
from config import Config
from input_manager import InputManager
from ai_processor import AIProcessor
from concept_manager import ConceptManager
from note_generator import ObsidianNoteGenerator
from timestamp_linker import TimestampLinker

class LawExamNoteProcessor:
    def __init__(self):
        self.input_manager = InputManager()
        # 用于字幕处理的AI模型
        self.subtitle_ai_processor = AIProcessor(
            Config.SUBTITLE_PROCESSING_API_KEY, 
            Config.SUBTITLE_PROCESSING_BASE_URL, 
            Config.SUBTITLE_PROCESSING_MODEL
        )
        # 用于概念增强的AI模型
        self.concept_enhancement_ai_processor = AIProcessor(
            Config.CONCEPT_ENHANCEMENT_API_KEY, 
            Config.CONCEPT_ENHANCEMENT_BASE_URL, 
            Config.CONCEPT_ENHANCEMENT_MODEL
        )
        self.concept_manager = ConceptManager(Config.OBSIDIAN_VAULT_PATH)
        # 注意：这里不需要预先指定输出路径，会在处理时动态指定
        self.note_generator = ObsidianNoteGenerator("temp")  # 临时路径
        self.timestamp_linker = TimestampLinker(Config.OBSIDIAN_VAULT_PATH)
        
        # 添加SiliconFlow增强器（延迟初始化）
        self.siliconflow_enhancer = None
    
    def process_subtitle_file(self):
        """处理单个字幕文件的完整流程"""
        try:
            # 1. 获取用户输入
            subtitle_info = self.input_manager.get_subtitle_info()
            
            # 2. 读取字幕内容
            print("📖 读取字幕文件...")
            subtitle_content = self.input_manager.read_subtitle_file(subtitle_info['file_path'])
            
            if not subtitle_content.strip():
                print("❌ 字幕文件为空")
                return []
            
            # 3. 扫描现有概念库
            print("🔍 扫描现有概念库...")
            self.concept_manager.scan_existing_notes()
            existing_concepts = self.concept_manager.get_all_concepts_for_ai()
            
            # 4. AI处理：一次性提取所有知识点 (使用字幕处理模型)
            print("🤖 AI正在分析字幕内容，提取知识点...")
            all_notes = self.subtitle_ai_processor.extract_all_knowledge_points(
                subtitle_content, subtitle_info
            )
            
            if not all_notes:
                print("❌ 未能提取到知识点，请检查字幕内容")
                return []
            
            print(f"✅ 提取到 {len(all_notes)} 个知识点")
            
            # 5. AI增强：优化概念关系 (使用概念增强模型)
            print("🔗 AI正在优化概念关系...")
            enhanced_notes = self.concept_enhancement_ai_processor.enhance_concept_relationships(
                all_notes, existing_concepts
            )
            
            # 6. 生成笔记文件（保存到指定科目文件夹）
            print(f"📝 生成笔记文件到: {subtitle_info['subject_folder']}")
            created_files = []
            for note_data in enhanced_notes:
                # 确保yaml_front_matter存在，并添加course_url
                if 'yaml_front_matter' not in note_data:
                    note_data['yaml_front_matter'] = {}
                note_data['yaml_front_matter']['course_url'] = subtitle_info['course_url']

                file_path = self.note_generator.create_note_file(
                    note_data, 
                    subtitle_info['output_path']  # 使用科目特定的输出路径
                )
                created_files.append(file_path)
            
            # 7. 更新概念数据库
            self.concept_manager.update_database(enhanced_notes)
            
            print(f"\n🎉 成功生成 {len(created_files)} 个笔记文件")
            print(f"📁 保存位置: {subtitle_info['output_path']}")
            
            # 显示生成的文件列表
            print("\n📋 生成的笔记:")
            for file_path in created_files:
                filename = os.path.basename(file_path)
                print(f"  • {filename}")
            
            # 8. 自动进行时间戳链接化处理
            if subtitle_info['course_url']:
                print("\n🔗 自动进行时间戳链接化处理...")
                self.timestamp_linker.process_subject_notes(subtitle_info['subject'])
                print("✅ 时间戳链接化处理完成。")

            return created_files
            
        except Exception as e:
            print(f"❌ 处理过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_siliconflow_enhancer(self):
        """获取SiliconFlow增强器实例（延迟初始化）"""
        if self.siliconflow_enhancer is None:
            try:
                from siliconflow_concept_enhancer import SiliconFlowConceptEnhancer
                self.siliconflow_enhancer = SiliconFlowConceptEnhancer(
                    Config.SILICONFLOW_API_KEY,
                    self.concept_enhancement_ai_processor, # 使用概念增强AI处理器
                    self.concept_manager
                )
                print("✅ SiliconFlow BGE增强器已初始化")
            except ImportError as e:
                print(f"❌ 无法导入SiliconFlow增强器: {e}")
                return None
            except Exception as e:
                print(f"❌ 初始化SiliconFlow增强器失败: {e}")
                return None
        return self.siliconflow_enhancer
    
    def enhance_existing_notes(self):
        """使用AI增强现有笔记的概念关系（支持多种模式）"""
        print("\n🔄 增强现有笔记的概念关系")
        print("="*50)
        
        # 先尝试加载现有概念数据库
        if not self.concept_manager.load_database_from_file():
            print("📚 概念数据库不存在，重新扫描...")
            self.concept_manager.scan_existing_notes()
        
        print("请选择增强方式:")
        print("1. 传统方式（发送所有概念给AI）")
        print("2. BGE混合检索（embedding召回+reranker精排）🔥 推荐")
        print("3. 返回主菜单")
        
        method_choice = input("请选择方式 (1-3): ").strip()
        
        if method_choice == '2':
            self._enhance_with_hybrid_search()
        elif method_choice == '1':
            self._enhance_traditional()
        elif method_choice == '3':
            return
        else:
            print("❌ 无效选择")
    
    def _enhance_with_hybrid_search(self):
        """使用BGE混合检索增强笔记"""
        print("\n🔖 BGE混合检索模式（embedding召回+reranker精排）")
        
        enhancer = self._get_siliconflow_enhancer()
        if enhancer is None:
            print("❌ 无法启动BGE增强器，请检查配置")
            return
        
        print("\n⚙️ 参数配置:")
        print("1. 使用默认参数（召回100个，精排15个，阈值0.98）⭐ 推荐")
        print("2. 自定义参数")
        print("3. 返回")
        
        config_choice = input("请选择 (1-3): ").strip()
        
        if config_choice == '2':
            try:
                print("\n📝 自定义参数:")
                embedding_top_k = int(input("  embedding召回数量 (建议50-200，默认100): ") or "100")
                rerank_top_k = int(input("  reranker精排数量 (建议10-20，默认15): ") or "15")
                rerank_threshold = float(input("  reranker分数阈值 (建议0.2-0.5，默认0.98): ") or "0.98")
                
                print(f"\n✅ 已设置: 召回{embedding_top_k}个 → 精排{rerank_top_k}个 → 阈值{rerank_threshold}")
            except ValueError:
                print("❌ 参数格式错误，使用默认值")
                embedding_top_k, rerank_top_k, rerank_threshold = 100, 15, 0.98
        elif config_choice == '1':
            embedding_top_k, rerank_top_k, rerank_threshold = 100, 15, 0.98
            print("\n✅ 使用默认参数: 召回100个 → 精排15个 → 阈值0.98")
        else:
            return
        
        print("\n📂 选择处理范围:")
        print("1. 增强所有科目的笔记")
        print("2. 增强特定科目的笔记")
        print("3. 返回")
        
        choice = input("请选择操作 (1-3): ").strip()
        
        if choice == '1':
            notes = self._collect_all_law_notes()
            if notes:
                print(f"\n🚀 开始处理 {len(notes)} 个笔记...")
                enhancer.batch_enhance_with_hybrid_search(
                    notes, False, embedding_top_k, rerank_top_k, rerank_threshold
                )
            else:
                print("❌ 没有找到需要处理的笔记")
        elif choice == '2':
            subject = self._select_subject()
            if subject:
                notes = self._collect_subject_notes_by_name(subject)
                if notes:
                    print(f"\n🚀 开始处理 {subject} 的 {len(notes)} 个笔记...")
                    enhancer.batch_enhance_with_hybrid_search(
                        notes, False, embedding_top_k, rerank_top_k, rerank_threshold
                    )
                else:
                    print(f"❌ {subject} 科目下没有找到笔记")
        
        # 重新扫描更新概念数据库
        if choice in ['1', '2']:
            print(f"\n📚 重新扫描更新概念数据库...")
            self.concept_manager.scan_existing_notes()
    
    def _enhance_traditional(self):
        """传统方式增强笔记"""
        print("\n📖 传统增强模式（发送所有概念给AI）")
        print("1. 增强所有科目的笔记")
        print("2. 增强特定科目的笔记")
        print("3. 返回")
        
        choice = input("请选择操作 (1-3): ").strip()
        
        if choice == '1':
            self._enhance_all_notes()
        elif choice == '2':
            self._enhance_specific_subject()
        elif choice == '3':
            return
        else:
            print("❌ 无效选择")
    
    def _select_subject(self):
        """选择科目"""
        print("\n📚 选择要处理的科目:")
        subjects = list(Config.SUBJECT_MAPPING.keys())
        
        for i, subject in enumerate(subjects, 1):
            folder_name = Config.get_subject_folder_name(subject)
            print(f"  {i:2d}. {subject} ({folder_name})")
        
        try:
            choice = int(input(f"请选择科目 (1-{len(subjects)}): ").strip())
            if 1 <= choice <= len(subjects):
                return subjects[choice - 1]
            else:
                print("❌ 无效选择")
                return None
        except ValueError:
            print("❌ 请输入有效数字")
            return None
    
    def _collect_subject_notes_by_name(self, subject: str):
        """根据科目名称收集笔记"""
        subject_folder = Config.get_subject_folder_name(subject)
        subject_path = os.path.join(Config.OBSIDIAN_VAULT_PATH, subject_folder)
        
        if not os.path.exists(subject_path):
            print(f"❌ 科目文件夹不存在: {subject_folder}")
            return []
        
        notes = []
        for root, dirs, files in os.walk(subject_path):
            for file in files:
                if file.endswith('.md') and file not in ["概念数据库.md", "概念嵌入缓存_BGE.json"]:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 提取标题
                        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                        if yaml_match:
                            yaml_data = yaml.safe_load(yaml_match.group(1))
                            title = yaml_data.get('title', os.path.splitext(file)[0])
                        else:
                            title = os.path.splitext(file)[0]
                        
                        notes.append({
                            'title': title,
                            'file_path': file_path,
                            'content': content,
                            'subject': subject
                        })
                    except Exception as e:
                        print(f"⚠️ 读取失败 {file}: {e}")
        
        return notes
    
    def _enhance_all_notes(self):
        """增强所有科目的笔记"""
        print("\n🔄 开始增强所有法考笔记的概念关系...")
        
        # 收集所有笔记
        all_notes = self._collect_all_law_notes()
        
        if not all_notes:
            print("❌ 没有找到需要增强的笔记")
            return
        
        print(f"📝 找到 {len(all_notes)} 个笔记需要处理")
        confirm = input("确认继续？(y/N): ").strip().lower()
        
        if confirm != 'y':
            print("🚫 操作已取消")
            return
        
        self._process_notes_enhancement(all_notes)
    
    def _enhance_specific_subject(self):
        """增强特定科目的笔记"""
        print("\n📚 选择要增强的科目:")
        subjects = list(Config.SUBJECT_MAPPING.keys())
        
        for i, subject in enumerate(subjects, 1):
            folder_name = Config.get_subject_folder_name(subject)
            print(f"  {i:2d}. {subject} ({folder_name})")
        
        try:
            choice = int(input(f"请选择科目 (1-{len(subjects)}): ").strip())
            if 1 <= choice <= len(subjects):
                selected_subject = subjects[choice - 1]
                self._enhance_subject_notes(selected_subject)
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")
    
    def _enhance_subject_notes(self, subject: str):
        """增强特定科目的笔记"""
        print(f"\n🔄 增强 {subject} 科目的笔记...")
        
        subject_folder = Config.get_subject_folder_name(subject)
        subject_path = os.path.join(Config.OBSIDIAN_VAULT_PATH, subject_folder)
        
        if not os.path.exists(subject_path):
            print(f"❌ 科目文件夹不存在: {subject_folder}")
            return
        
        # 收集该科目的笔记
        notes = []
        for root, dirs, files in os.walk(subject_path):
            for file in files:
                if file.endswith('.md') and file != "概念数据库.md":
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 提取标题
                        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                        if yaml_match:
                            yaml_data = yaml.safe_load(yaml_match.group(1))
                            title = yaml_data.get('title', os.path.splitext(file)[0])
                        else:
                            title = os.path.splitext(file)[0]
                        
                        notes.append({
                            'title': title,
                            'file_path': file_path,
                            'content': content,
                            'subject': subject
                        })
                    except Exception as e:
                        print(f"⚠️ 读取失败 {file}: {e}")
        
        if not notes:
            print(f"❌ {subject} 科目下没有找到笔记")
            return
        
        print(f"📝 找到 {len(notes)} 个 {subject} 笔记")
        self._process_notes_enhancement(notes)
    
    def _collect_all_law_notes(self):
        """收集所有法考笔记"""
        notes = []
        
        for subject_name, folder_name in Config.SUBJECT_MAPPING.items():
            subject_path = os.path.join(Config.OBSIDIAN_VAULT_PATH, folder_name)
            
            if not os.path.exists(subject_path):
                continue
            
            for root, dirs, files in os.walk(subject_path):
                for file in files:
                    if file.endswith('.md') and file != "概念数据库.md":
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 提取标题
                            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                            if yaml_match:
                                yaml_data = yaml.safe_load(yaml_match.group(1))
                                title = yaml_data.get('title', os.path.splitext(file)[0])
                            else:
                                title = os.path.splitext(file)[0]
                            
                            notes.append({
                                'title': title,
                                'file_path': file_path,
                                'content': content,
                                'subject': subject_name
                            })
                            
                        except Exception as e:
                            print(f"⚠️ 读取笔记失败 {file_path}: {e}")
        
        return notes
    
    def _process_notes_enhancement(self, notes):
        """批量处理笔记增强"""
        existing_concepts = self.concept_manager.get_all_concepts_for_ai()
        
        enhanced_count = 0
        failed_count = 0
        
        for i, note_info in enumerate(notes, 1):
            print(f"\n🔄 处理 {i}/{len(notes)}: {note_info['title']}")
            
            try:
                # 传统增强方式也使用概念增强AI处理器
                enhancement_result = self.concept_enhancement_ai_processor.enhance_single_note_concepts(
                    note_info['content'], 
                    note_info['title'],
                    existing_concepts
                )
                
                if enhancement_result and enhancement_result.get('modified', False):
                    # 备份原文件
                    backup_path = note_info['file_path'] + '.backup'
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(note_info['content'])
                    
                    # 写入增强后的内容
                    with open(note_info['file_path'], 'w', encoding='utf-8') as f:
                        f.write(enhancement_result['enhanced_content'])
                    
                    # 删除备份文件（如果写入成功）
                    os.remove(backup_path)
                    
                    enhanced_count += 1
                    print(f"  ✅ 增强成功")
                else:
                    print(f"  ⚠️ 无需修改")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ❌ 增强失败: {e}")
        
        print(f"\n🎉 处理完成！")
        print(f"  ✅ 成功增强: {enhanced_count} 个")
        print(f"  ⚠️ 无需修改: {len(notes) - enhanced_count - failed_count} 个")
        print(f"  ❌ 处理失败: {failed_count} 个")
        
        if enhanced_count > 0:
            print(f"\n📚 重新扫描更新概念数据库...")
            self.concept_manager.scan_existing_notes()
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("🎓 法考字幕转Obsidian笔记处理器")
        print("="*60)
        print("📁 保存路径:", Config.OBSIDIAN_VAULT_PATH)
        print("="*60)
        print("1. 处理新字幕文件")
        print("2. 增强现有笔记关系 (开发中)")
        print("3. 显示科目文件夹映射")
        print("4. 退出")
        print("="*60)
    
    def show_subject_mapping(self):
        """显示科目文件夹映射"""
        print("\n📚 科目文件夹映射:")
        print("-" * 40)
        for subject, folder in Config.SUBJECT_MAPPING.items():
            folder_path = Config.get_output_path(subject)
            exists = "✅" if os.path.exists(folder_path) else "📁"
            print(f"  {exists} {subject} -> {folder}")
        print("-" * 40)
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*60)
        print("🎓 法考字幕转Obsidian笔记处理器")
        print("="*60)
        print("📁 保存路径:", Config.OBSIDIAN_VAULT_PATH)
        print("="*60)
        print("1. 处理新字幕文件")
        print("2. 增强现有笔记关系")  # 已完成开发
        print("3. 时间戳链接化处理")  # 新增功能
        print("4. 显示科目文件夹映射")
        print("5. 查看概念数据库")  # 新增功能
        print("6. 退出")
        print("="*60)
    
    def process_timestamps(self):
        """时间戳链接化处理"""
        print("\n🔗 时间戳链接化处理")
        print("="*50)
        
        print("1. 处理所有科目的笔记")
        print("2. 处理特定科目的笔记")
        print("3. 返回主菜单")
        
        choice = input("请选择操作 (1-3): ").strip()
        
        if choice == '1':
            self._process_all_timestamps()
        elif choice == '2':
            self._process_subject_timestamps()
        elif choice == '3':
            return
        else:
            print("❌ 无效选择")
    
    def _process_all_timestamps(self):
        """处理所有笔记的时间戳"""
        print("\n🔗 开始处理所有笔记的时间戳链接...")
        
        result = self.timestamp_linker.process_all_notes_with_course_url()
        
        if result['total'] == 0:
            print("💡 提示：请确保笔记的YAML中包含course_url字段")
            print("   例如：course_url: \"https://www.bilibili.com/video/BV1xxx\"")
    
    def _process_subject_timestamps(self):
        """处理特定科目的时间戳"""
        print("\n📚 选择要处理的科目:")
        subjects = list(Config.SUBJECT_MAPPING.keys())
        
        for i, subject in enumerate(subjects, 1):
            folder_name = Config.get_subject_folder_name(subject)
            print(f"  {i:2d}. {subject} ({folder_name})")
        
        try:
            choice = int(input(f"请选择科目 (1-{len(subjects)}): ").strip())
            if 1 <= choice <= len(subjects):
                selected_subject = subjects[choice - 1]
                result = self.timestamp_linker.process_subject_notes(selected_subject)
                
                if result['total'] == 0:
                    print("💡 提示：请确保笔记的YAML中包含course_url字段")
                    print("   例如：course_url: \"https://www.bilibili.com/video/BV1xxx\"")
            else:
                print("❌ 无效选择")
        except ValueError:
            print("❌ 请输入有效数字")

    def show_concept_database_status(self):
        """查看概念数据库"""
        print("\n📊 概念数据库状态")
        print("-" * 40)
        
        # 尝试加载数据库
        if self.concept_manager.load_database_from_file():
            total_concepts = len(self.concept_manager.concept_database)
            print(f"✅ 数据库已存在: {total_concepts} 个概念")
            
            # 按科目统计
            subject_stats = {}
            for concept, data in self.concept_manager.concept_database.items():
                subject = data.get('subject', '未知')
                subject_stats[subject] = subject_stats.get(subject, 0) + 1
            
            print("\n📚 各科目概念统计:")
            for subject, count in sorted(subject_stats.items()):
                folder_name = Config.get_subject_folder_name(subject) if subject in Config.SUBJECT_MAPPING else subject
                print(f"  {folder_name}: {count} 个概念")
            
            # 检查两个数据库文件的状态
            print(f"\n📄 数据库文件状态:")
            
            # Markdown文件
            md_file = os.path.join(Config.OBSIDIAN_VAULT_PATH, "概念数据库.md")
            if os.path.exists(md_file):
                file_size = os.path.getsize(md_file) / 1024  # KB
                mtime = os.path.getmtime(md_file)
                last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  📝 概念数据库.md: {file_size:.1f} KB (更新: {last_modified})")
            else:
                print(f"  📝 概念数据库.md: ❌ 不存在")
            
            # JSON文件
            json_file = os.path.join(Config.OBSIDIAN_VAULT_PATH, "概念数据库.json")
            if os.path.exists(json_file):
                file_size = os.path.getsize(json_file) / 1024  # KB
                mtime = os.path.getmtime(json_file)
                last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  📊 概念数据库.json: {file_size:.1f} KB (更新: {last_modified})")
            else:
                print(f"  📊 概念数据库.json: ❌ 不存在")
                
        else:
            print("❌ 概念数据库不存在")
            print("💡 建议: 先处理一些字幕文件或运行笔记增强功能来建立数据库")
        
        print("-" * 40)
    
    def run(self):
        """主运行函数"""
        # 确保基础目录存在
        Config.ensure_directories()
        
        while True:
            self.show_menu()
            
            try:
                choice = input("请选择操作 (1-6): ").strip()
                
                if choice == '1':
                    self.process_subtitle_file()
                elif choice == '2':
                    self.enhance_existing_notes()
                elif choice == '3':
                    self.process_timestamps()
                elif choice == '4':
                    self.show_subject_mapping()
                elif choice == '5':
                    self.show_concept_database_status()
                elif choice == '6':
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请重新输入")
                
            except KeyboardInterrupt:
                print("\n👋 程序已中断，再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    # 检查必要的依赖
    try:
        import openai
        import yaml
    except ImportError as e:
        print(f"❌ 缺少必要依赖: {e}")
        print("请运行: pip install openai pyyaml")
        exit(1)
    
    processor = LawExamNoteProcessor()
    processor.run()
