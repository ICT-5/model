from db_utils import fetch_questions, start_session, log_question, log_answer, end_session, upsert_free_text_question
from llm_utils import generate_follow_up_questions, init_llm_chain

chain = init_llm_chain()

# ----------------------------
# 1) 세션 시작 & 질문 뽑기
# ----------------------------
def start_interview(user_id, interview_type):
    questions = fetch_questions(interview_type)
    session_id = start_session(user_id, total_questions=5)
    return session_id, questions

# ----------------------------
# 2) 단일 답변 & 꼬리질문 생성
# ----------------------------
def answer_and_followup(session_id, question_id, answer, keywords, interview_type, personality):
    sim_q_id = log_question(session_id, question_id)
    log_answer(sim_q_id, answer)

    follow_up = generate_follow_up_questions(chain, "직전질문", answer, keywords, interview_type, personality)
    tmp_qid = upsert_free_text_question(follow_up, interview_type)
    tmp_sim_qid = log_question(session_id, tmp_qid)

    return follow_up, tmp_qid

# ----------------------------
# 3) 자동 인터뷰 루프 (질문 5개 × 꼬리질문 2개)
# ----------------------------
#def run_full_interview(user_id, interview_type, personality, keywords):
#    questions = fetch_questions(interview_type)
#    session_id = start_session(user_id, total_questions=len(questions))
#
#    results = []
#
#    for q_id, q_text, itype in questions:
#        sim_q_id = log_question(session_id, q_id)
#        answer = f"(자동생성) {q_text} 에 대한 답변"
#        log_answer(sim_q_id, answer)
#
#        q_record = {
#            "main_question": q_text,
#            "user_answer": answer,
#            "follow_ups": []
#        }
#
#        last_answer = answer
#        for i in range(2):
#            follow_up = generate_follow_up_questions(
#                chain, q_text, last_answer, keywords, itype, personality
#            )
#            tmp_q_id = upsert_free_text_question(follow_up, itype)
#            tmp_sim_q_id = log_question(session_id, tmp_q_id)
#
#            follow_ans = f"(자동생성) {follow_up} 에 대한 답변"
#            log_answer(tmp_sim_q_id, follow_ans)
#
#            q_record["follow_ups"].append({
#                "follow_up": follow_up,
#                "answer": follow_ans
#            })
#            last_answer = follow_ans
#
#        results.append(q_record)
#
#    end_session(session_id, reason="limit_reached")
#    return {"session_id": session_id, "results": results}