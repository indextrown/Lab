
# streamlit run 7.\ streamlitChat.py 
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1️⃣ 환경변수 로드 (.env에서 API 키 불러옴)
load_dotenv()

# 학습시킨 AI
def LLM(user_message):

    # 2️⃣ 임베딩 모델
    embedding = OpenAIEmbeddings(model="text-embedding-3-large")

    # 3️⃣ Pinecone 기존 인덱스 불러오기
    index_name = "tax-index"
    database = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embedding
    )

    # 4️⃣ LLM 초기화
    llm = ChatOpenAI(model="gpt-4o")

    # 5️⃣ 사용자 단어 → 세무 용어 변환용 사전
    dictionary = {
        "직장인": "거주자",
        "근로자": "거주자",
        "월급": "근로소득",
        "세금": "소득세"
    }

    # 6️⃣ 질문을 변환하기 위한 사전 체인
    prompt = ChatPromptTemplate.from_template("""
    사용자의 질문을 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
    만약 변경할 필요가 없다고 판단된다면, 사용자의 질문을 변경하지 않아도 됩니다.
    그런 경우에는 질문만 리턴해주세요.

    사전: {dictionary}
    질문: {question}
    """)

    dictionary_chain = prompt | llm | StrOutputParser()

    # 7️⃣ 변환된 질문 생성
    new_query = dictionary_chain.invoke({
        "dictionary": dictionary,
        "question": user_message
    })

    # 8️⃣ 벡터DB에서 관련 문서 검색
    retrieved_docs = database.similarity_search(new_query, k=3)

    # 9️⃣ 문서 내용 합치기
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])

    # 🔟 최종 RAG 프롬프트 구성
    rag_prompt_template = PromptTemplate(
        template="""
        You are a helpful assistant that can answer questions about Korean tax law.
        Use the following context to answer accurately and concisely in Korean.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """,
        input_variables=["context", "question"]
    )

    # 11️⃣ 체인 연결
    rag_chain = rag_prompt_template | llm | StrOutputParser()

    # 12️⃣ 답변 생성
    ai_message = rag_chain.invoke({
        "context": context_text,
        "question": new_query
    })

    return ai_message

# 여기서부터는 그냥 UI
st.set_page_config(page_title="소득세 챗봇", page_icon="📚")
st.title("📚 소득세 챗봇")
st.caption("소득세에 관련된 모든것을 답변해드립니다!")

if 'message_list' not in st.session_state:
    st.session_state.message_list = []

# print(f"before == {st.session_state.message_list}")
for message in st.session_state.message_list:
    with st.chat_message(message['role']):
        st.write(message['content'])

if user_question := st.chat_input(placeholder="소득세에 관련된 궁금한 내용들을 말씀해주세요!"):
    with st.chat_message("user"):
        st.write(user_question)
    st.session_state.message_list.append({"role": "user", "content": user_question})

    with st.spinner("답변을 생성하는 중입니다"):
        # AI 답변
        ai_message = LLM(user_question)
        with st.chat_message("ai"):
            st.write(ai_message)
        st.session_state.message_list.append({"role": "ai", "content": ai_message})


        
# print(f"after == {st.session_state.message_list}")