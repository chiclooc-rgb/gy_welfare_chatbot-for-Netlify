#!/usr/bin/env python3
# standalone_chatbot.py - 패키지 의존성 없는 챗봇 (Python 내장 모듈만 사용)

import json
import re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import webbrowser
from threading import Timer

# 키워드 확장 맵 (개선된 기능!)
KEYWORD_EXPANSION = {
    "다자녀가정": ["다자녀", "셋째아이", "3자녀", "3명 이상", "많은 자녀", "자녀 3명", "세 자녀"],
    "다자녀": ["다자녀가정", "셋째아이", "3자녀", "3명 이상", "많은 자녀"],
    "혜택": ["지원", "보조", "급여", "수당", "할인", "감면", "우대", "바우처"],
    "지원": ["혜택", "보조", "급여", "수당", "지원금", "보조금"],
    "임신": ["임산부", "예비맘", "산모", "임신부", "태교"],
    "출산": ["분만", "해산", "신생아", "산후조리", "출산휴가"],
    "육아": ["양육", "자녀돌봄", "보육", "육아휴직", "돌봄"],
    "보육": ["어린이집", "유치원", "놀이방", "육아", "양육"],
    "교육": ["학습", "교육비", "학비", "수업료", "교육지원"],
    "의료": ["건강", "진료", "치료", "병원", "의료비", "건강검진"],
    "주거": ["주택", "임대", "전세", "주거비", "주거지원", "주거복지"],
    "노인": ["어르신", "고령자", "노령", "시니어", "65세", "노인복지"],
    "장애인": ["장애", "장애우", "특수교육", "재활", "장애인복지"],
    "저소득": ["기초생활", "차상위", "소득", "빈곤", "경제적어려움"],
    "청년": ["20대", "30대", "청소년", "대학생", "청년지원"],
    "여성": ["여성복지", "모성", "여성지원", "성평등"],
    "한부모": ["한부모가정", "미혼모", "편부모", "조손가정"]
}

class ChatbotServer:
    def __init__(self):
        self.texts = []
        self.metas = []
        self.conversation_history = []
        self.load_documents()
    
    def load_documents(self):
        """문서 로드"""
        index_dir = Path("index")
        try:
            # simple_meta.json 파일 로드
            with open(index_dir / "simple_meta.json", "r", encoding="utf-8") as f:
                store = json.load(f)
            self.metas = store["metas"]
            self.texts = store["texts"]
            print(f"✅ 문서 로드 완료: {len(self.texts)}개 청크")
        except Exception as e:
            print(f"❌ 문서 로드 실패: {e}")
            # 테스트 데이터 생성
            self.texts = [
                "다자녀 가정 지원: 셋째 자녀부터 양육비 월 10만원 지원합니다. 3자녀 이상 가정에게는 추가 혜택이 있습니다.",
                "임산부 지원: 임신 중 의료비 지원 및 출산 준비금을 지급합니다. 예비맘들을 위한 다양한 프로그램이 있습니다.",
                "육아휴직 지원: 최대 12개월 육아휴직 급여를 지원합니다. 양육과 돌봄을 위한 휴직 제도입니다.",
                "보육료 지원: 어린이집 이용료를 소득별로 차등 지원합니다. 유치원 교육비도 포함됩니다.",
                "출산지원금: 출산 시 200만원의 지원금을 지급합니다. 신생아 양육을 위한 기본 지원입니다.",
                "한부모가정 지원: 한부모 가정을 위한 생활비 지원 및 자녀 교육비를 지원합니다.",
                "노인복지: 65세 이상 어르신을 위한 의료비 지원 및 생활 서비스를 제공합니다.",
                "장애인복지: 장애인을 위한 재활 서비스 및 생활 지원 프로그램이 있습니다."
            ]
            self.metas = [{"source": "테스트문서", "chunk_id": i} for i in range(len(self.texts))]
            print("📝 테스트 데이터로 초기화")
    
    def expand_query(self, query):
        """쿼리 확장 (개선된 기능!)"""
        expanded_terms = []
        query_lower = query.lower()
        
        for keyword, synonyms in KEYWORD_EXPANSION.items():
            if keyword in query_lower:
                expanded_terms.extend(synonyms)
            for synonym in synonyms:
                if synonym in query_lower and keyword not in expanded_terms:
                    expanded_terms.append(keyword)
                    expanded_terms.extend([s for s in synonyms if s != synonym])
        
        if expanded_terms:
            unique_terms = list(set(expanded_terms))
            expanded_query = f"{query} {' '.join(unique_terms[:5])}"
            return expanded_query
        
        return query
    
    def search_documents(self, query, top_k=5):
        """문서 검색 (키워드 기반)"""
        expanded_query = self.expand_query(query)
        print(f"🔍 원본 쿼리: {query}")
        print(f"🔍 확장된 쿼리: {expanded_query}")
        
        scores = []
        keywords = expanded_query.lower().split()
        
        for i, text in enumerate(self.texts):
            score = 0
            text_lower = text.lower()
            for keyword in keywords:
                if keyword in text_lower:
                    score += text_lower.count(keyword)
            
            if score > 0:
                scores.append({
                    "rank": i + 1,
                    "score": score,
                    "text": text,
                    "source": self.metas[i]["source"],
                    "chunk_id": self.metas[i]["chunk_id"]
                })
        
        # 점수순 정렬
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]
    
    def extract_relevant_content(self, text, query):
        """쿼리와 관련된 부분만 추출"""
        lines = text.split('\n')
        query_keywords = query.lower().split()
        
        # 사업 구분자 찾기
        program_blocks = []
        current_block = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 새로운 사업 시작 감지
            if (line.startswith(tuple('0123456789')) and '. ' in line) or \
               ('□ 대상:' in line and current_block):
                if current_block:
                    program_blocks.append('\n'.join(current_block))
                    current_block = []
            
            current_block.append(line)
        
        if current_block:
            program_blocks.append('\n'.join(current_block))
        
        # 가장 관련성 높은 블록 찾기
        best_block = ""
        best_score = 0
        
        for block in program_blocks:
            score = 0
            block_lower = block.lower()
            for keyword in query_keywords:
                if keyword in block_lower:
                    score += block_lower.count(keyword) * 2
            
            # 추가 관련 키워드 점수
            for keyword in self.expand_query(query).split():
                if keyword.lower() in block_lower:
                    score += 1
                    
            if score > best_score:
                best_score = score
                best_block = block
        
        return best_block if best_block else text[:500]

    def extract_multiple_programs(self, search_results, query, max_programs=5):
        """여러 관련 사업을 추출"""
        programs = []
        query_keywords = query.lower().split()
        
        for result in search_results[:10]:  # 상위 10개 결과에서 찾기
            text = result['text']
            lines = text.split('\n')
            
            # 사업 구분자 찾기
            program_blocks = []
            current_block = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 새로운 사업 시작 감지
                if (line.startswith(tuple('0123456789')) and '. ' in line) or \
                   ('□ 대상:' in line and current_block):
                    if current_block:
                        program_blocks.append('\n'.join(current_block))
                        current_block = []
                
                current_block.append(line)
            
            if current_block:
                program_blocks.append('\n'.join(current_block))
            
            # 각 블록의 관련성 점수 계산
            for block in program_blocks:
                score = 0
                block_lower = block.lower()
                for keyword in query_keywords:
                    if keyword in block_lower:
                        score += block_lower.count(keyword) * 2
                
                # 추가 관련 키워드 점수
                for keyword in self.expand_query(query).split():
                    if keyword.lower() in block_lower:
                        score += 1
                
                if score > 0:
                    # 중복 제거 (제목으로 비교)
                    title = ""
                    for line in block.split('\n'):
                        if line.strip() and not line.strip().startswith('□'):
                            title = line.strip()
                            break
                    
                    # 이미 있는 프로그램인지 확인
                    is_duplicate = False
                    for existing in programs:
                        if title and title in existing['content']:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and title:
                        programs.append({
                            'content': block,
                            'score': score,
                            'title': title,
                            'source': result['source']
                        })
        
        # 점수순 정렬 후 상위 max_programs개 반환
        programs.sort(key=lambda x: x['score'], reverse=True)
        return programs[:max_programs]

    def markdown_to_html(self, text):
        """간단한 마크다운을 HTML로 변환"""
        # 제목 변환
        text = text.replace('### ', '<h3>')
        text = text.replace('## ', '<h2>')
        
        # 볼드 변환
        import re
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # 이모지 줄바꿈 처리
        text = text.replace('□ ', '<br/>□ ')
        text = text.replace('🔹 ', '<br/>🔹 ')
        
        # 구분선
        text = text.replace('---', '<hr/>')
        
        # 줄바꿈을 <br/>로 변환
        text = text.replace('\n', '<br/>')
        
        return text

    def classify_program_type(self, content, query):
        """프로그램을 전용/우대/관련으로 분류"""
        content_lower = content.lower()
        query_lower = query.lower()
        
        # 쿼리에서 대상 추출
        target_type = ""
        if '다자녀' in query_lower:
            target_type = "다자녀"
        elif '한부모' in query_lower:
            target_type = "한부모"
        elif '임신' in query_lower or '임산부' in query_lower or '출산' in query_lower:
            target_type = "임신출산"
        elif '보육' in query_lower or '어린이집' in query_lower:
            target_type = "보육"
        
        if not target_type:
            return "관련"
        
        # 전용 정책 판단 (대상이 명시적으로 해당 대상만을 위한 것)
        if target_type == "다자녀":
            if any(keyword in content_lower for keyword in ['다자녀가정', '다자녀 가정', '셋째아이', '3자녀']):
                if any(exclusive in content_lower for exclusive in ['만을 대상', '다자녀만', '다자녀가정 대상']):
                    return "전용"
                elif '다자녀' in content_lower and '대상' in content_lower:
                    return "전용"
        elif target_type == "한부모":
            if any(keyword in content_lower for keyword in ['한부모가정', '한부모 가정', '모자가정', '부자가정']):
                if any(exclusive in content_lower for exclusive in ['만을 대상', '한부모만', '한부모가정 대상']):
                    return "전용"
                elif '한부모' in content_lower and '대상' in content_lower:
                    return "전용"
        elif target_type == "임신출산":
            if any(keyword in content_lower for keyword in ['임산부', '임신부', '출산', '신생아', '임신', '해산', '분만', '산후조리', '출산비', '임신축하']):
                if any(exclusive in content_lower for exclusive in ['임산부 대상', '출산 지원', '임산부', '출산']):
                    return "전용"
        elif target_type == "보육":
            if any(keyword in content_lower for keyword in ['어린이집', '보육료', '보육지원']):
                if any(exclusive in content_lower for exclusive in ['보육 대상', '어린이집 대상']):
                    return "전용"
        
        # 우대 정책 판단 (일반 정책에서 우대 조건)
        if any(pref in content_lower for pref in ['우대', '가점', '우선', '추가 지원']):
            if target_type == "다자녀" and '다자녀' in content_lower:
                return "우대"
            elif target_type == "한부모" and '한부모' in content_lower:
                return "우대"
            elif target_type == "임신출산" and any(k in content_lower for k in ['임산부', '출산', '임신', '해산', '분만', '산후조리']):
                return "우대"
            elif target_type == "보육" and any(k in content_lower for k in ['보육', '어린이집']):
                return "우대"
        
        # 키워드가 있으면 관련, 없으면 무관련
        if target_type == "다자녀" and any(k in content_lower for k in ['다자녀', '셋째', '3자녀']):
            return "관련"
        elif target_type == "한부모" and any(k in content_lower for k in ['한부모', '모자', '부자']):
            return "관련"
        elif target_type == "임신출산" and any(k in content_lower for k in ['임신', '임산부', '출산', '신생아', '해산', '분만', '산후조리', '출산비', '임신축하']):
            return "관련"
        elif target_type == "보육" and any(k in content_lower for k in ['보육', '어린이집', '아동']):
            return "관련"
        
        return "무관련"

    def format_single_program(self, content, program_type="관련"):
        """단일 프로그램 정보를 포맷팅 (분류 포함)"""
        lines = content.split('\n')
        structured_info = {
            'title': '',
            'target': '',
            'content': '',
            'method': '',
            'contact': '',
            'note': ''
        }
        
        for line in lines:
            line = line.strip()
            # 넘버링 제거 (숫자. 형태)
            if line and '.' in line and line.split('.', 1)[0].isdigit():
                line = line.split('.', 1)[1].strip()
            
            if '대상:' in line:
                structured_info['target'] = line.replace('□ 대상:', '').strip()
            elif '내용:' in line:
                structured_info['content'] = line.replace('□ 내용:', '').strip()
            elif '방법:' in line:
                structured_info['method'] = line.replace('□ 방법:', '').strip()
            elif '문의:' in line:
                structured_info['contact'] = line.replace('□ 문의:', '').strip()
            elif '※' in line:
                structured_info['note'] = line.replace('※', '').strip()
            elif line and not line.startswith('□') and not structured_info['title']:
                structured_info['title'] = line
        
        # 분류별 이모지
        type_emoji = {
            "전용": "🎯",
            "우대": "🔖", 
            "관련": "💡"
        }
        
        # 컴팩트한 형태로 구성
        emoji = type_emoji.get(program_type, "📋")
        program_html = f"<h4>{emoji} {structured_info['title']}</h4>"
        
        if structured_info['target']:
            program_html += f"<strong>🎯 대상:</strong> {structured_info['target']}<br/>"
        
        if structured_info['content']:
            program_html += f"<strong>💡 내용:</strong> {structured_info['content']}<br/>"
        
        if structured_info['method']:
            program_html += f"<strong>📝 신청:</strong> {structured_info['method']}<br/>"
        
        if structured_info['contact']:
            program_html += f"<strong>📞 문의:</strong> {structured_info['contact']}<br/>"
        
        if structured_info['note']:
            program_html += f"<strong>⚠️ 참고:</strong> {structured_info['note']}<br/>"
        
        return program_html

    def generate_multiple_programs_answer(self, query, programs):
        """여러 프로그램을 분류별로 그룹화하여 답변 생성"""
        query_lower = query.lower()
        
        # 프로그램들을 분류별로 그룹화
        classified_programs = {
            "전용": [],
            "우대": [],
            "관련": []
        }
        
        for program in programs:
            program_type = self.classify_program_type(program['content'], query)
            if program_type in classified_programs:
                classified_programs[program_type].append(program)
        
        # 대상별 맞춤 인사말
        if '다자녀' in query_lower:
            target_name = "다자녀가정"
        elif '한부모' in query_lower:
            target_name = "한부모가정"
        elif '임신' in query_lower or '임산부' in query_lower:
            target_name = "임신·출산"
        elif '보육' in query_lower:
            target_name = "보육"
        else:
            target_name = "관련"
        
        total_count = sum(len(progs) for progs in classified_programs.values())
        answer = f"<h3>🎯 {target_name} 지원정책 {total_count}개를 분류별로 안내해드립니다</h3>"
        
        # 1. 전용 정책 (최우선)
        if classified_programs["전용"]:
            answer += f"<h3>🎯 {target_name} 전용 정책 ({len(classified_programs['전용'])}개)</h3>"
            answer += "<p><em>해당 대상만을 위한 특화 지원 정책입니다</em></p>"
            for program in classified_programs["전용"]:
                answer += f"<div style='margin: 10px 0; padding: 12px; border-left: 4px solid #dc2626; background: #fef2f2;'>"
                answer += self.format_single_program_with_summary(program['content'], "전용")
                answer += "</div>"
        
        # 2. 우대 정책 (차순위)
        if classified_programs["우대"]:
            answer += f"<h3>🔖 {target_name} 우대 혜택 ({len(classified_programs['우대'])}개)</h3>"
            answer += "<p><em>일반 정책에서 우대 조건을 받을 수 있는 정책입니다</em></p>"
            for program in classified_programs["우대"]:
                answer += f"<div style='margin: 10px 0; padding: 12px; border-left: 4px solid #2563eb; background: #eff6ff;'>"
                answer += self.format_single_program_with_summary(program['content'], "우대")
                answer += "</div>"
        
        # 3. 관련 정책 (참고)
        if classified_programs["관련"]:
            answer += f"<h3>💡 관련 지원 정책 ({len(classified_programs['관련'])}개)</h3>"
            answer += "<p><em>간접적으로 도움이 될 수 있는 정책입니다</em></p>"
            for program in classified_programs["관련"]:
                answer += f"<div style='margin: 10px 0; padding: 12px; border-left: 4px solid #059669; background: #f0fdf4;'>"
                answer += self.format_single_program_with_summary(program['content'], "관련")
                answer += "</div>"
        
        # 맞춤형 마무리 멘트
        if classified_programs["전용"]:
            answer += "<strong>💬 상담사 한마디:</strong><br/>"
            answer += f"{target_name} 전용 정책을 우선적으로 확인해보시고, 우대 혜택도 함께 신청하시면 더욱 도움이 될 거예요! "
            answer += "구체적인 신청 방법이나 자격 요건이 궁금하시면 언제든 말씀해주세요."
        else:
            answer += "<strong>💬 상담사 한마디:</strong><br/>"
            answer += f"{target_name} 관련해서 더 구체적인 정보가 필요하시면 언제든 말씀해주세요!"
        
        return answer

    def generate_answer(self, query, search_results):
        """답변 생성 (여러 프로그램 표시)"""
        if not search_results:
            return "<h3>❌ 죄송합니다</h3>관련 정보를 찾을 수 없습니다.<br/><strong>💡 팁:</strong> 다른 키워드로 다시 시도해보세요."
        
        # 여러 관련 프로그램 추출
        programs = self.extract_multiple_programs(search_results, query, max_programs=5)
        
        if not programs:
            # 프로그램을 찾지 못한 경우 기존 방식으로
            best_result = search_results[0]
            return f"<h3>🔍 관련 정보</h3>{best_result['text'][:300]}...<br/><small>📖 출처: {best_result['source']}</small>"
        
        # 여러 프로그램 답변 생성
        answer = self.generate_multiple_programs_answer(query, programs)
        
        # 출처 정보 추가 (간단하게)
        sources = list(set([p['source'] for p in programs[:3]]))
        answer += f"<br/><hr/><small>📖 <strong>출처:</strong> {', '.join(sources)}</small>"
        
        return answer
    
    def analyze_question_intent(self, question):
        """질문 의도 분석"""
        question_lower = question.lower()
        
        # 특정 정책 상세 설명 요청 패턴
        detail_patterns = [
            '설명해줘', '설명해', '알려줘', '알려주세요', '뭐야', '뭔가요', '무엇인가요',
            '자세히', '상세히', '구체적으로', '어떤 내용', '어떤거야', '어떤건가요',
            '에 대해서', '에 대해', '관해서', '관해'
        ]
        
        # 추가/더보기 요청 패턴  
        more_patterns = [
            '다른거', '더 있어', '더 있나', '또 있어', '또 있나', '다른', '추가로', 
            '더', '또', '외에', '말고', '이외에'
        ]
        
        # 특정 정책명이 포함되어 있고 상세 설명 요청인 경우
        if any(pattern in question_lower for pattern in detail_patterns):
            # 정책명 추출 시도
            potential_policy = ""
            if '부모급여' in question_lower:
                potential_policy = "부모급여"
            elif '다자녀' in question_lower:
                potential_policy = "다자녀"
            elif '한부모' in question_lower:
                potential_policy = "한부모"
            elif '임신' in question_lower or '임산부' in question_lower:
                potential_policy = "임신출산"
            elif '보육' in question_lower:
                potential_policy = "보육"
            
            if potential_policy:
                return "detail", potential_policy
        
        # 추가 정보 요청인 경우
        if any(pattern in question_lower for pattern in more_patterns):
            return "more", ""
        
        # 기본은 목록 요청
        return "list", ""

    def generate_detail_answer(self, question, search_results, target_policy):
        """특정 정책에 대한 상세 설명 답변"""
        if not search_results:
            return f"<h3>❌ 죄송합니다</h3>{target_policy} 관련 정보를 찾을 수 없습니다."
        
        # 가장 관련성 높은 결과 선택
        best_result = search_results[0]
        relevant_content = self.extract_relevant_content(best_result['text'], question)
        
        # 상세 설명 답변 생성
        answer = f"<h3>📋 {target_policy} 상세 안내</h3>"
        
        # 정책 내용을 구조화해서 제공
        lines = relevant_content.split('\n')
        structured_info = {
            'title': '',
            'target': '',
            'content': '',
            'amount': '',
            'method': '',
            'contact': '',
            'note': ''
        }
        
        for line in lines:
            line = line.strip()
            if line and '.' in line and line.split('.', 1)[0].isdigit():
                line = line.split('.', 1)[1].strip()
            
            if '대상:' in line:
                structured_info['target'] = line.replace('□ 대상:', '').strip()
            elif '내용:' in line:
                structured_info['content'] = line.replace('□ 내용:', '').strip()
            elif '금액:' in line or '지원액:' in line:
                structured_info['amount'] = line.replace('□ 금액:', '').replace('□ 지원액:', '').strip()
            elif '방법:' in line:
                structured_info['method'] = line.replace('□ 방법:', '').strip()
            elif '문의:' in line:
                structured_info['contact'] = line.replace('□ 문의:', '').strip()
            elif '※' in line:
                structured_info['note'] = line.replace('※', '').strip()
            elif line and not line.startswith('□') and not structured_info['title']:
                structured_info['title'] = line
        
        # 상세 내용 구성
        if structured_info['title']:
            answer += f"<h4>🎯 {structured_info['title']}</h4>"
        
        if structured_info['target']:
            answer += f"<div style='margin: 15px 0; padding: 15px; background: #f0f9ff; border-left: 4px solid #0ea5e9;'>"
            answer += f"<strong>👥 지원 대상</strong><br/>{structured_info['target']}</div>"
        
        if structured_info['content']:
            answer += f"<div style='margin: 15px 0; padding: 15px; background: #f0fdf4; border-left: 4px solid #22c55e;'>"
            answer += f"<strong>💰 지원 내용</strong><br/>{structured_info['content']}</div>"
        
        if structured_info['amount']:
            answer += f"<div style='margin: 15px 0; padding: 15px; background: #fef3c7; border-left: 4px solid #f59e0b;'>"
            answer += f"<strong>💵 지원 금액</strong><br/>{structured_info['amount']}</div>"
        
        if structured_info['method']:
            answer += f"<div style='margin: 15px 0; padding: 15px; background: #f3e8ff; border-left: 4px solid #a855f7;'>"
            answer += f"<strong>📝 신청 방법</strong><br/>{structured_info['method']}</div>"
        
        if structured_info['contact']:
            answer += f"<div style='margin: 15px 0; padding: 15px; background: #fecaca; border-left: 4px solid #ef4444;'>"
            answer += f"<strong>📞 문의처</strong><br/>{structured_info['contact']}</div>"
        
        if structured_info['note']:
            answer += f"<div style='margin: 15px 0; padding: 15px; background: #fee2e2; border-left: 4px solid #dc2626;'>"
            answer += f"<strong>⚠️ 주의사항</strong><br/>{structured_info['note']}</div>"
        
        # 추가 질문 유도
        answer += "<div style='margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 8px;'>"
        answer += "<strong>💬 더 궁금한 점이 있으시면:</strong><br/>"
        answer += f"• \"{target_policy} 신청 방법이 더 자세히 알고 싶어요\"<br/>"
        answer += f"• \"{target_policy} 신청 서류는 뭐가 필요한가요?\"<br/>"
        answer += f"• \"다른 {target_policy} 관련 혜택도 있나요?\"<br/>"
        answer += "언제든 물어보세요!</div>"
        
        return answer

    def generate_more_answer(self, question, search_results):
        """추가 정보 요청에 대한 답변"""
        # 이전 대화에서 언급된 주제 찾기
        recent_topics = []
        for msg in self.conversation_history[-4:]:  # 최근 4개 메시지 확인
            if msg['role'] == 'user':
                if '다자녀' in msg['content']:
                    recent_topics.append('다자녀')
                elif '한부모' in msg['content']:
                    recent_topics.append('한부모')
                elif '임신' in msg['content'] or '임산부' in msg['content']:
                    recent_topics.append('임신출산')
                elif '보육' in msg['content']:
                    recent_topics.append('보육')
        
        if recent_topics:
            # 이전 주제와 관련된 추가 정보 제공
            last_topic = recent_topics[-1]
            modified_question = f"{last_topic} 관련 추가 지원 정책"
            programs = self.extract_multiple_programs(search_results, modified_question, max_programs=5)
            
            answer = f"<h3>💡 {last_topic} 관련 추가 지원 정책을 찾아드렸어요!</h3>"
            
            if programs:
                for program in programs:
                    program_type = self.classify_program_type(program['content'], modified_question)
                    
                    answer += f"<div style='margin: 10px 0; padding: 12px; border-left: 4px solid #6366f1; background: #f1f5f9;'>"
                    answer += self.format_single_program_with_summary(program['content'], program_type)
                    answer += "</div>"
                
                answer += "<strong>💬 이 중에서 더 자세히 알고 싶은 정책이 있으시면 말씀해주세요!</strong>"
            else:
                answer += f"<p>현재 찾을 수 있는 {last_topic} 관련 추가 정책이 없습니다.</p>"
                answer += f"<strong>💬 다른 주제의 지원 정책이 궁금하시면 언제든 말씀해주세요!</strong>"
        else:
            # 일반적인 추가 정보 제공
            answer = "<h3>🔍 다른 지원 정책들을 더 찾아보시겠어요?</h3>"
            answer += "<p>이런 주제들도 문의하실 수 있어요:</p>"
            answer += "<ul>"
            answer += "<li>🏠 <strong>주거 지원 정책</strong> - \"주거 지원 혜택\"</li>"
            answer += "<li>👶 <strong>육아 지원 정책</strong> - \"육아 지원 혜택\"</li>"
            answer += "<li>🎓 <strong>교육 지원 정책</strong> - \"교육비 지원\"</li>"
            answer += "<li>💼 <strong>취업 지원 정책</strong> - \"취업 지원 프로그램\"</li>"
            answer += "</ul>"
            answer += "<strong>💬 궁금한 주제를 말씀해주시면 관련 정책을 찾아드릴게요!</strong>"
        
        return answer

    def format_single_program_with_summary(self, content, program_type="관련"):
        """프로그램 정보를 간단한 요약과 함께 포맷팅"""
        lines = content.split('\n')
        structured_info = {
            'title': '',
            'target': '',
            'content': '',
            'summary': ''
        }
        
        for line in lines:
            line = line.strip()
            if line and '.' in line and line.split('.', 1)[0].isdigit():
                line = line.split('.', 1)[1].strip()
            
            if '대상:' in line:
                structured_info['target'] = line.replace('□ 대상:', '').strip()
            elif '내용:' in line:
                structured_info['content'] = line.replace('□ 내용:', '').strip()
            elif line and not line.startswith('□') and not structured_info['title']:
                structured_info['title'] = line
        
        # 간단한 요약 생성 (더 자세하게)
        if structured_info['content'] or structured_info['target']:
            summary_parts = []
            if structured_info['target']:
                target_text = structured_info['target'][:50] if len(structured_info['target']) > 50 else structured_info['target']
                summary_parts.append(f"대상: {target_text}")
            if structured_info['content']:
                content_text = structured_info['content'][:80] if len(structured_info['content']) > 80 else structured_info['content']
                summary_parts.append(f"내용: {content_text}")
            structured_info['summary'] = "<br/>".join(summary_parts) if summary_parts else ""
        
        # 분류별 이모지
        type_emoji = {"전용": "🎯", "우대": "🔖", "관련": "💡"}
        emoji = type_emoji.get(program_type, "📋")
        
        program_html = f"<h4>{emoji} {structured_info['title']}</h4>"
        if structured_info['summary']:
            program_html += f"<p style='color: #6b7280; font-size: 14px; margin: 5px 0;'>{structured_info['summary']}</p>"
        
        return program_html

    def ask_question(self, question):
        """질문 처리 (의도 분석 포함)"""
        # 대화 히스토리에 추가
        self.conversation_history.append({"role": "user", "content": question})
        
        # 질문 의도 분석
        intent, target = self.analyze_question_intent(question)
        
        # 문서 검색
        search_results = self.search_documents(question)
        
        # 의도에 따른 답변 생성
        if intent == "detail" and target:
            answer = self.generate_detail_answer(question, search_results, target)
        elif intent == "more":
            answer = self.generate_more_answer(question, search_results)
        else:
            answer = self.generate_answer(question, search_results)
        
        # 대화 히스토리에 답변 추가
        self.conversation_history.append({"role": "assistant", "content": answer})
        
        # 최근 10개 대화만 유지
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return {
            "answer": answer,
            "sources": search_results,
            "conversation_length": len(self.conversation_history)
        }

# 글로벌 챗봇 인스턴스
chatbot = ChatbotServer()

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 복지 상담 챗봇 (실제 버전)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            height: 100vh;
            background: #f8fafc;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: white;
            padding: 1rem;
            border-bottom: 1px solid #e2e8f0;
            text-align: center;
        }
        
        .header h1 {
            color: #1e293b;
            font-size: 1.5rem;
            margin-bottom: 0.25rem;
        }
        
        .status {
            background: #10b981;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            display: inline-block;
            margin-top: 0.5rem;
        }
        
        .chat-container {
            flex: 1;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
            display: flex;
            flex-direction: column;
            padding: 1rem;
        }
        
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: white;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .message {
            margin-bottom: 1rem;
            display: flex;
            gap: 0.75rem;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            flex-shrink: 0;
        }
        
        .message.user .message-avatar {
            background: #3b82f6;
            color: white;
        }
        
        .message.bot .message-avatar {
            background: #10b981;
            color: white;
        }
        
        .message-content {
            max-width: 70%;
            background: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            line-height: 1.6;
        }
        
        .message-content h3, .message-content h4 {
            margin: 0.5rem 0;
            color: #1e293b;
        }
        
        .message-content hr {
            margin: 1rem 0;
            border: none;
            border-top: 1px solid #e2e8f0;
        }
        
        .message-content strong {
            color: #374151;
        }
        
        .message-content small {
            color: #6b7280;
        }
        
        .message.user .message-content {
            background: #3b82f6;
            color: white;
        }
        
        .input-area {
            display: flex;
            gap: 0.75rem;
            align-items: flex-end;
        }
        
        .input-field {
            flex: 1;
            padding: 0.75rem;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 1rem;
            resize: none;
            min-height: 50px;
        }
        
        .input-field:focus {
            outline: none;
            border-color: #3b82f6;
        }
        
        .send-btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-size: 1rem;
            cursor: pointer;
            height: 50px;
        }
        
        .send-btn:hover {
            background: #2563eb;
        }
        
        .loading {
            display: none;
            text-align: center;
            color: #64748b;
            padding: 1rem;
        }
        
        .info-box {
            background: #eff6ff;
            border: 1px solid #3b82f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 복지 상담 챗봇</h1>
        <div class="status">✨ 실제 문서 검색 + 개선된 기능</div>
        <p style="margin-top: 0.5rem; color: #64748b;">
            실제 복지 문서를 검색하여 정확한 답변을 제공합니다
        </p>
    </div>
    
    <div class="chat-container">
        <div class="info-box">
            <strong>🚀 적용된 개선 기능:</strong><br>
            ✅ 쿼리 확장: "다자녀가정" → "다자녀 + 셋째아이 + 3자녀 + 지원 + 혜택"<br>
            ✅ 대화 기억: 이전 대화를 기억하고 연관된 답변 제공<br>
            ✅ 실제 문서 검색: 복지 관련 실제 문서에서 정보 검색
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message bot">
                <div class="message-avatar">🤖</div>
                <div class="message-content">안녕하세요! 생애복지플랫폼 상담 챗봇입니다. 💬

복지 혜택, 지원 프로그램 등에 대해 궁금한 것을 질문해주세요!

지금은 실제 문서 검색과 개선된 기능들이 적용된 상태입니다. 😊</div>
            </div>
        </div>
        
        <div id="loading" class="loading">
            답변을 생성하고 있습니다...
        </div>
        
        <div class="input-area">
            <textarea id="messageInput" class="input-field" placeholder="예: 다자녀가정 혜택이 뭐가 있나요?" rows="1"></textarea>
            <button id="sendBtn" class="send-btn">전송</button>
        </div>
    </div>

    <script>
        const chatArea = document.getElementById('chatArea');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const loading = document.getElementById('loading');
        
        function addMessage(type, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = type === 'user' ? '👤' : '🤖';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            
            // 봇 메시지는 HTML로 렌더링, 사용자 메시지는 텍스트로
            if (type === 'bot') {
                messageContent.innerHTML = content;
            } else {
                messageContent.textContent = content;
            }
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage('user', message);
            messageInput.value = '';
            sendBtn.disabled = true;
            loading.style.display = 'block';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: message })
                });
                
                const data = await response.json();
                addMessage('bot', data.answer);
                
            } catch (error) {
                addMessage('bot', '죄송합니다. 오류가 발생했습니다: ' + error.message);
            } finally {
                sendBtn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    </script>
</body>
</html>
            '''
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/ask' and self.command == 'POST':
            self.do_POST()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/ask':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                question = data.get('question', '')
                
                result = chatbot.ask_question(question)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                response = json.dumps(result, ensure_ascii=False)
                self.wfile.write(response.encode('utf-8'))
                
            except Exception as e:
                self.send_error(500, str(e))

def run_server():
    server = HTTPServer(('localhost', 8000), RequestHandler)
    print("🚀 챗봇 서버가 시작되었습니다!")
    print("📱 브라우저에서 http://localhost:8000 에 접속하세요")
    print("💡 이제 실제 문서 검색과 개선된 기능들을 사용할 수 있습니다!")
    
    # 3초 후 자동으로 브라우저 열기
    def open_browser():
        webbrowser.open('http://localhost:8000')
    
    Timer(3.0, open_browser).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다.")
        server.shutdown()

if __name__ == '__main__':
    run_server()


