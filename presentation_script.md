# Script thuyết trình: AI Agent hỗ trợ học Cấu trúc dữ liệu và Giải thuật

## Slide 1: Giới thiệu đề tài

Em xin chào thầy/cô và các bạn.  
Hôm nay em xin trình bày đề tài **AI Agent hỗ trợ học Cấu trúc dữ liệu và Giải thuật**.

Mục tiêu của đề tài là xây dựng một hệ thống trợ giảng AI hỗ trợ người học trong quá trình giải bài tập DSA. Điểm khác biệt của hệ thống là không tập trung đưa ra lời giải trực tiếp, mà hướng tới việc dẫn dắt người học suy nghĩ theo phương pháp Socratic.

Về công nghệ, hệ thống sử dụng Python cho phần lõi agent, LangGraph để tổ chức workflow, Gemini API làm LLM provider và Streamlit để xây dựng giao diện tương tác.

## Slide 2: Vấn đề và hướng tiếp cận

Khi học Cấu trúc dữ liệu và Giải thuật, người học thường không chỉ gặp khó ở việc biết thuật toán nào cần dùng. Khó khăn lớn hơn nằm ở việc phân tích đề, nhận ra ràng buộc, chọn cấu trúc dữ liệu phù hợp, kiểm tra edge case và tự đánh giá độ phức tạp.

Nếu dùng chatbot thông thường, hệ thống có thể trả lời rất nhanh, nhưng dễ đưa luôn lời giải hoặc code mẫu. Điều này giúp người học có đáp án, nhưng lại không giúp hình thành tư duy giải bài.

Vì vậy, hướng tiếp cận của đề tài là xây dựng một **AI tutor** có workflow, có trạng thái học tập và có lớp kiểm soát chất lượng. Hệ thống sẽ đặt câu hỏi, sinh gợi ý từng bước, tạo testcase để người học tự kiểm và hạn chế đưa lời giải hoàn chỉnh trong chế độ mặc định.

## Slide 3: Cơ sở lý thuyết

Cơ sở đầu tiên của hệ thống là phương pháp **Socratic tutoring**. Thay vì nói thẳng đáp án, tutor sẽ đặt câu hỏi gợi mở để người học tự phát hiện hướng giải.

Trong bài toán thuật toán, cách này rất phù hợp. Ví dụ, thay vì nói ngay công thức hoặc code, hệ thống có thể hỏi: input và output là gì, ràng buộc cho phép thuật toán độ phức tạp bao nhiêu, hoặc nếu trace một ví dụ nhỏ thì cần lưu trạng thái nào.

Cơ sở thứ hai là **LLM Agent có trạng thái**. LLM giúp hiểu ngôn ngữ tự nhiên, nhưng nếu chỉ gọi LLM trực tiếp thì hệ thống khó kiểm soát. Vì vậy, project tổ chức LLM trong một workflow có state.

Cơ sở thứ ba là kiến trúc **multi-agent**. Mỗi agent đảm nhiệm một vai trò riêng như phân loại đề, sinh testcase, kiểm code hoặc review phản hồi. Cách tách này giúp hệ thống dễ mở rộng và dễ debug hơn.

## Slide 4: Mục tiêu hệ thống

Hệ thống có bốn mục tiêu chính.

Thứ nhất là điều phối hội thoại bằng LangGraph. Workflow được tách thành nhiều node theo intent, ví dụ gửi đề bài, xin gợi ý, gửi code hoặc yêu cầu lời giải trực tiếp.

Thứ hai là sử dụng LLM cho các tác vụ cần hiểu ngữ cảnh như detect intent, classify problem, generate hint, generate testcase và review phản hồi.

Thứ ba là xây dựng Quality Layer. Lớp này gồm Testcase Generator, Execution Validator và Pedagogy Critic để kiểm soát chất lượng trước khi phản hồi tới người học.

Thứ tư là cung cấp giao diện tương tác bằng Streamlit, hỗ trợ nhiều phiên chat, hiển thị trạng thái học tập và Agent Trace.

## Slide 5: Công nghệ sử dụng

Về công nghệ, phần lõi hệ thống được viết bằng Python. Python được dùng để định nghĩa agent, state, schema dữ liệu, validator và các test tự động.

LangGraph được dùng để điều phối workflow. Thay vì xử lý toàn bộ logic trong một hàm lớn, hệ thống chia thành các node riêng. Điều này giúp workflow rõ ràng và dễ mở rộng.

Gemini API được sử dụng như LLM provider. LLM tham gia vào các bước như nhận diện intent, phân loại bài toán, sinh gợi ý, sinh testcase và review phản hồi sư phạm.

Streamlit được dùng cho giao diện chat. Đây là lựa chọn phù hợp vì project cần một giao diện demo nhanh, có thể hiển thị hội thoại, state, testcase, validation result và Agent Trace.

Ngoài ra, hệ thống có Quality Layer và sandbox execution để chạy code Python trên testcase khi có expected output. Các thành phần cốt lõi được kiểm thử bằng unittest.

## Slide 6: Kiến trúc tổng quan

Về kiến trúc, hệ thống được chia thành năm lớp chính.

Lớp đầu tiên là **User Interface**, nơi người học gửi đề bài, câu hỏi, code hoặc yêu cầu gợi ý.

Lớp thứ hai là **Tutor Orchestration Layer**. Đây là trung tâm điều phối, trong đó AI Tutor Agent nhận input, gọi LLM để xác định intent, cập nhật state và chọn agent phù hợp.

Lớp thứ ba là **Learning Modules**, gồm các module như Problem Classifier, Hint Generator và Code Analyzer.

Lớp thứ tư là **Quality Layer**, gồm Testcase Generator, Execution Validator và Pedagogy Critic.

Lớp cuối cùng là **State & Memory Layer**, lưu các thông tin như bài hiện tại, dạng bài, hint level, attempts, testcase history và validation result.

## Slide 7: Workflow LangGraph

Slide này minh họa workflow LangGraph của hệ thống.

Đầu tiên, input của người học đi vào node `detect_intent`. Node này dùng LLM để xác định người học đang gửi đề bài, xin gợi ý, gửi code, hỏi lý thuyết hay yêu cầu lời giải trực tiếp.

Sau đó, graph dùng conditional edge để route sang node tương ứng. Ví dụ, nếu intent là `SUBMIT_PROBLEM` thì chuyển sang node `submit_problem`. Nếu là `REQUEST_HINT` thì chuyển sang `request_hint`. Nếu là `SUBMIT_CODE` thì chuyển sang `submit_code`.

Mỗi node xử lý một nhiệm vụ riêng rồi đi về node `finalize`. Cách tổ chức này giúp hệ thống không bị gom toàn bộ logic vào một agent duy nhất, đồng thời thể hiện rõ tính agentic trong quá trình xử lý.

## Slide 8: Các agent chính

Hệ thống gồm nhiều agent hoặc module chuyên trách.

**Intent Detector Agent** phân loại ý định của người học.  
**Problem Classifier Agent** nhận diện dạng bài và pattern thuật toán.  
**Hint Generator Agent** sinh gợi ý theo hint level và trạng thái hiện tại.  
**Testcase Generator Agent** tạo testcase để trace hoặc validate.  
**Execution Validator Agent** chạy code Python khi có testcase đủ expected output.  
**Pedagogy Critic Agent** kiểm tra phản hồi có quá trực tiếp hoặc lộ lời giải không.  
Cuối cùng, **Session Title Agent** sinh tiêu đề ngắn cho mỗi phiên chat.

Điểm quan trọng là các agent này không hoạt động rời rạc. AI Tutor Agent sẽ điều phối chúng theo workflow và tổng hợp kết quả thành phản hồi cuối cho người học.

## Slide 9: State & Memory

Một thành phần quan trọng của hệ thống là `LearningState`.

State lưu các thông tin như `current_problem`, `problem_type`, `concepts`, `hint_level`, `student_attempts`, `generated_tests`, `latest_validation`, `pedagogy_flags` và `agent_trace`.

Nhờ có state, hệ thống có thể phản hồi theo ngữ cảnh. Ví dụ, cùng một câu “cho em thêm gợi ý”, nếu người học mới xin lần đầu thì hệ thống chỉ hỏi định hướng. Nhưng nếu đã xin nhiều lần, hệ thống có thể đưa gợi ý cụ thể hơn.

State cũng giúp UI hiển thị tiến trình học tập, ví dụ hint level hiện tại, dạng bài, testcase đã sinh và kết quả validation gần nhất.

## Slide 10: Quality Layer

Quality Layer là lớp giúp hệ thống kiểm soát chất lượng phản hồi.

Đầu tiên là **Testcase Generator**. Agent này sinh các testcase basic, edge, adversarial hoặc stress. Testcase được chia thành hai loại: `validation` và `trace_only`. Validation testcase có expected output để chạy tự động, còn trace-only testcase dùng để người học tự kiểm logic.

Thứ hai là **Execution Validator**. Thành phần này chạy code Python trong sandbox có timeout và trả về các trạng thái như `PASSED`, `FAILED`, `RUNTIME_ERROR`, `TIMEOUT` hoặc `SKIPPED`.

Thứ ba là **Pedagogy Critic**. Agent này review phản hồi nháp trước khi gửi. Nếu phản hồi lộ full solution, quá trực tiếp hoặc không phù hợp hint level, hệ thống sẽ yêu cầu LLM viết lại.

Nhờ Quality Layer, hệ thống không phụ thuộc hoàn toàn vào một lần sinh phản hồi của LLM.

## Slide 11: Kết quả đạt được

Đến hiện tại, hệ thống đã đạt được một số kết quả chính.

Thứ nhất, hệ thống đã có kiến trúc multi-agent rõ ràng cho bài toán DSA tutor.

Thứ hai, workflow LangGraph đã được tách node theo intent, giúp quá trình xử lý dễ quan sát và dễ mở rộng.

Thứ ba, hệ thống có cơ chế gợi ý nhiều cấp độ theo phương pháp Socratic, hạn chế việc đưa full solution.

Thứ tư, Quality Layer đã có đủ ba thành phần chính: testcase generation, code validation và pedagogy review.

Thứ năm, hệ thống có giao diện Streamlit hỗ trợ nhiều phiên chat, panel trạng thái học tập và Agent Trace.

Ngoài ra, các thành phần chính đã có test tự động để kiểm tra schema, validator và luồng xử lý agent.

## Slide 12: Hạn chế và hướng phát triển

Bên cạnh các kết quả đã đạt được, hệ thống vẫn còn một số hạn chế.

Thứ nhất, hệ thống chưa có database bền vững để lưu lịch sử học tập dài hạn. Hiện tại state chủ yếu phục vụ từng phiên tương tác.

Thứ hai, sandbox execution mới tập trung vào Python và còn đơn giản. Nếu triển khai thực tế, cần môi trường cách ly mạnh hơn, giới hạn tài nguyên rõ hơn và hỗ trợ thêm ngôn ngữ lập trình.

Thứ ba, testcase expected output vẫn phụ thuộc vào độ rõ của đề bài và khả năng sinh của LLM. Với một số bài chưa đủ thông tin, testcase chỉ nên dùng để trace thay vì validate tự động.

Hướng phát triển tiếp theo là bổ sung database, nâng cấp sandbox, xây dựng Evaluation Agent để chấm chất lượng phản hồi theo rubric, và xây benchmark DSA lớn hơn để đánh giá hệ thống một cách định lượng.

Tóm lại, DSA Socratic Agent đặt nền tảng cho một AI tutor có trạng thái, có workflow và có lớp kiểm soát chất lượng, hướng tới hỗ trợ người học phát triển tư duy giải thuật thay vì chỉ nhận đáp án.

Em xin kết thúc phần trình bày tại đây. Em cảm ơn thầy/cô và các bạn đã lắng nghe.

