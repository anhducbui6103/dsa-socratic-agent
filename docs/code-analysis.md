# Module phân tích code

## Mục tiêu

Module phân tích code giúp sinh viên nhìn lại cách tiếp cận của mình. Hệ thống không sửa code hoàn chỉnh, không thay sinh viên viết lại lời giải, mà đưa ra nhận xét và câu hỏi để sinh viên tự cải thiện.

## Đầu vào

- Đề bài hiện tại nếu có.
- Code sinh viên gửi.
- Ngôn ngữ lập trình.
- Ý tưởng sinh viên đã mô tả trước đó.
- Trạng thái hội thoại và mức gợi ý hiện tại.

## Đầu ra

- Tóm tắt ý tưởng mà code đang thể hiện.
- Nhận xét về độ phức tạp.
- Điểm có khả năng sai logic.
- Edge cases nên thử.
- Câu hỏi Socratic để sinh viên tự sửa.

## Các khía cạnh phân tích

### 1. Ý tưởng thuật toán

- Code đang dùng brute force, greedy, DP, DFS/BFS hay cấu trúc dữ liệu nào?
- Cách tiếp cận có phù hợp với ràng buộc không?
- Có biến/trạng thái nào thừa hoặc thiếu không?

### 2. Độ phức tạp

- Mỗi phần tử/đỉnh/cạnh được xử lý bao nhiêu lần?
- Có vòng lặp lồng nhau nào gây quá giới hạn không?
- Bộ nhớ phụ có tỷ lệ với kích thước input nào?

### 3. Tính đúng

- Điều kiện biên.
- Input rỗng hoặc kích thước 1.
- Trùng lặp.
- Giá trị âm/dương/lớn.
- Graph không liên thông, cây rỗng, chuỗi rỗng.

### 4. Khả năng tối ưu

- Có thể thay vòng lặp bằng hash map không?
- Có thể dùng stack để tránh duyệt lại không?
- Có thể lưu trạng thái DP tối giản hơn không?
- Có thể dùng binary search trên đáp án không?

## Mẫu phản hồi

```text
Code của em có vẻ đang đi theo hướng [tóm tắt ý tưởng].

Trước khi sửa chi tiết, em thử kiểm tra 2 điểm:
1. Mỗi phần tử đang được xử lý bao nhiêu lần?
2. Nếu input là [edge case], biến [tên biến] sẽ có giá trị gì?

Gợi ý nhỏ: thay vì tính lại [thông tin] ở mỗi bước, em có thể nghĩ cách lưu nó trong một cấu trúc dữ liệu phụ không?
```

## Giới hạn cần tuân thủ

- Không đưa code sửa hoàn chỉnh.
- Không nói "sai" một cách chung chung.
- Không chỉ đưa kết quả đúng/sai.
- Nên đưa ra tối đa 2-3 điểm cần sửa trong một lần để tránh quá tải.
