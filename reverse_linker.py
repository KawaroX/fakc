import os
import re
import math
from typing import List, Dict, Optional, Tuple, Any

class ReverseLinker:
    """反向关联增强器 - 专门为旧笔记添加新概念链接"""
    
    def __init__(self, siliconflow_enhancer, concept_manager):
        self.siliconflow_enhancer = siliconflow_enhancer
        self.concept_manager = concept_manager
    
    def add_reverse_links_for_new_notes(self, new_notes: List[Dict]) -> int:
        """为新概念建立反向链接"""
        print("🔗 开始为新概念建立反向链接...")
        
        # 提取所有新概念
        new_concepts = []
        for note in new_notes:
            concept_info = self._extract_concept_info_from_note(note)
            if concept_info:
                new_concepts.append(concept_info)
        
        if not new_concepts:
            print("⚠️ 未检测到新概念")
            return 0
        
        print(f"📝 检测到 {len(new_concepts)} 个新概念")
        
        # 为每个新概念找出相关旧笔记并添加链接
        total_links_added = 0
        for concept_info in new_concepts:
            links_added = self._add_reverse_links_for_concept(concept_info)
            total_links_added += links_added
        
        print(f"✅ 反向关联完成，共添加 {total_links_added} 个链接")
        return total_links_added
    
    def _collect_all_law_notes_for_reverse_linking(self) -> List[Dict[str, Any]]:
        """收集所有法考笔记用于反向链接"""
        from config import Config
        
        notes = []
        
        for subject_name, folder_name in Config.SUBJECT_MAPPING.items():
            subject_path = os.path.join(self.concept_manager.vault_path, folder_name)
            
            if not os.path.exists(subject_path):
                continue
            
            for root, dirs, files in os.walk(subject_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        
                        # 跳过错题文件
                        if '错题' in file_path:
                            continue
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 提取标题
                            yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                            if yaml_match:
                                try:
                                    import yaml
                                    yaml_data = yaml.safe_load(yaml_match.group(1))
                                    title = yaml_data.get('title', os.path.splitext(os.path.basename(file_path))[0])
                                except:
                                    title = os.path.splitext(os.path.basename(file_path))[0]
                            else:
                                title = os.path.splitext(os.path.basename(file_path))[0]
                            
                            notes.append({
                                'file_path': file_path,
                                'title': title,
                                'content': content,
                                'subject': subject_name
                            })
                            
                        except Exception as e:
                            print(f"    ⚠️ 跳过文件 {file_path}: {e}")
                            continue
        
        return notes
    
    def _extract_concept_info_from_note(self, note: Dict) -> Optional[Dict]:
        """从笔记中提取概念信息"""
        if 'yaml' not in note or not note['yaml'].get('title'):
            return None
            
        title = note['yaml']['title']
        # 移除科目前缀：【民法】善意取得 -> 善意取得
        concept_name = re.sub(r'^【[^】]+】', '', title).strip()
        
        # 构建用于相似度计算的描述文本
        description = self._build_concept_description(note)
        
        return {
            'name': concept_name,
            'full_title': title,
            'description': description,
            'content': note['content']
        }
    
    def _build_concept_description(self, note: Dict) -> str:
        """构建概念描述文本用于相似度计算"""
        description_parts = []
        
        # 添加标题
        if 'yaml' in note and note['yaml'].get('title'):
            description_parts.append(note['yaml']['title'])
        
        # 添加别名
        if 'yaml' in note and note['yaml'].get('aliases'):
            aliases = note['yaml']['aliases']
            if isinstance(aliases, list):
                description_parts.extend(aliases)
        
        # 添加标签
        if 'yaml' in note and note['yaml'].get('tags'):
            tags = note['yaml']['tags']
            if isinstance(tags, list):
                description_parts.extend(tags)
        
        # 添加内容的前200字符
        if 'content' in note:
            content_preview = note['content'][:200]
            description_parts.append(content_preview)
        
        return ' '.join(description_parts)
    
    def _add_reverse_links_for_concept(self, concept_info: Dict) -> int:
        """为单个概念添加反向链接"""
        concept_name = concept_info['name']
        concept_description = concept_info['description']
        
        print(f"  🔍 为概念'{concept_name}'寻找相关笔记...")
        
        # 使用BGE找出相关的旧笔记
        related_notes = self._find_related_old_notes(concept_description)
        
        if not related_notes:
            print(f"    ⚠️ 未找到相关笔记")
            return 0
        
        print(f"    📝 找到 {len(related_notes)} 个相关笔记")
        
        links_added = 0
        for note_path, similarity_score in related_notes[:8]:  # 限制为前8个最相关的
            if self._add_concept_link_to_note_file(note_path, concept_info['full_title'], concept_name):
                links_added += 1
                print(f"    ✅ 为 {os.path.basename(note_path)} 添加链接 (相似度: {similarity_score:.3f})")
        
        return links_added
    
    def _find_related_old_notes(self, concept_description: str, threshold: float = 0.4) -> List[Tuple[str, float]]:
        """使用BGE找出与概念相关的旧笔记"""
        # 获取概念的嵌入向量
        concept_embedding = self.siliconflow_enhancer.get_embedding(concept_description, "new_concept")
        if not concept_embedding:
            print("    ❌ 无法获取概念嵌入向量")
            return []
        
        # 获取所有现有笔记
        print("    📖 加载现有笔记...")
        all_notes = self._collect_all_law_notes_for_reverse_linking()
        print(f"    📝 找到 {len(all_notes)} 个现有笔记")
        
        if not all_notes:
            return []
        
        # 计算与所有现有笔记的相似度
        similar_notes = []
        processed_count = 0
        
        for note in all_notes:
            processed_count += 1
            if processed_count % 50 == 0:  # 每处理50个笔记显示一次进度
                print(f"    🔄 处理进度: {processed_count}/{len(all_notes)}")
            
            try:
                note_embedding = self.siliconflow_enhancer.get_embedding(note['content'], "note_content")
                if note_embedding:
                    similarity = self._cosine_similarity(concept_embedding, note_embedding)
                    if similarity > threshold:
                        similar_notes.append((note['file_path'], similarity))
            except Exception as e:
                print(f"    ⚠️ 处理笔记失败 {note['title']}: {e}")
                continue
        
        # 按相似度排序
        similar_notes.sort(key=lambda x: x[1], reverse=True)
        print(f"    ✅ 找到 {len(similar_notes)} 个相关笔记")
        
        return similar_notes
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _add_concept_link_to_note_file(self, note_path: str, full_title: str, concept_name: str) -> bool:
        """在笔记文件中添加概念链接"""
        try:
            # 读取文件内容
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已经存在该链接
            if f'[[{full_title}' in content or f'[[{concept_name}' in content:
                return False  # 已存在，跳过
            
            # 找到"相关概念"部分并添加链接
            updated_content = self._insert_concept_link(content, full_title, concept_name)
            
            if updated_content != content:
                # 备份并写入新内容
                backup_path = note_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                os.remove(backup_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 添加链接失败 {note_path}: {e}")
            return False
    
    def _insert_concept_link(self, content: str, full_title: str, concept_name: str) -> str:
        """在内容中插入概念链接"""
        # 构建链接文本
        link_text = f"[[{full_title}|{concept_name}]]"
        
        # 查找"相关概念"部分
        if "## 相关概念" in content:
            # 在相关概念部分末尾添加
            pattern = r'(## 相关概念\n)(.*?)((?=\n## |\n---|$))'
            
            def add_link(match):
                section_start = match.group(1)
                section_content = match.group(2).strip()
                section_end = match.group(3)
                
                if section_content:
                    return f"{section_start}{section_content}\n- {link_text}\n{section_end}"
                else:
                    return f"{section_start}- {link_text}\n{section_end}"
            
            updated = re.sub(pattern, add_link, content, flags=re.DOTALL)
            if updated != content:
                return updated
        
        # 如果没有"相关概念"部分，在文件末尾添加
        if not content.endswith('\n'):
            content += '\n'
        
        content += f"\n## 相关概念\n\n- {link_text}\n"
        return content