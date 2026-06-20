# Phân loại bài toán

## Mục đích

Phân loại bài toán giúp agent chọn câu hỏi và gợi ý phù hợp. Taxonomy không chỉ dựa trên tên chủ đề, mà dựa trên mẫu tư duy cần để giải bài.

## Nhóm bài toán đề xuất

| Nhóm | Dấu hiệu | Gợi ý Socratic mẫu |
| --- | --- | --- |
| Array / String | Duyệt dãy, chỉ số, subarray, substring | "Em cần theo dõi thông tin nào khi đi qua từng vị trí?" |
| Two Pointers | Mảng sắp xếp, cặp phần tử, cửa sổ trái/phải | "Khi nào con trỏ trái/phải nên di chuyển?" |
| Sliding Window | Đoạn con liên tiếp, tối ưu độ dài/tổng | "Cửa sổ hiện tại hợp lệ khi nào?" |
| Hash Map / Set | Tìm nhanh, đếm tần suất, kiểm tra tồn tại | "Khóa và giá trị trong bảng băm nên biểu diễn điều gì?" |
| Stack | Dấu hiệu ngoặc, nearest greater/smaller, undo | "Phần tử nào cần được giữ lại để so sánh với phần tử sau?" |
| Queue / BFS | Duyệt theo lớp, shortest path không trọng số | "Trạng thái nào nên được đưa vào hàng đợi tiếp theo?" |
| Tree / DFS | Đệ quy, cây nhị phân, duyệt cây | "Kết quả tại một nút phụ thuộc vào kết quả nào từ con trái/con phải?" |
| Graph | Đỉnh, cạnh, thành phần liên thông, chu trình | "Em đã biểu diễn quan hệ giữa các đối tượng thành graph như thế nào?" |
| Greedy | Chọn cục bộ, sắp xếp theo tiêu chí | "Lựa chọn cục bộ này có ảnh hưởng đến các bước sau ra sao?" |
| Dynamic Programming | Bài toán con lặp lại, tối ưu, đếm số cách | "Trạng thái nhỏ nhất nào đủ để mô tả bài toán con?" |
| Sorting / Searching | Cần thứ tự, binary search, sắp xếp tiêu chí | "Tính chất nào cho phép em loại bỏ một nửa không gian tìm kiếm?" |

## Thuộc tính cần trích xuất từ đề bài

- Đối tượng chính: mảng, chuỗi, cây, đồ thị, danh sách liên kết.
- Mục tiêu: tìm kiếm, đếm, tối ưu, kiểm tra tồn tại, xây dựng kết quả.
- Ràng buộc: kích thước input, miền giá trị, thời gian mong muốn.
- Yêu cầu liên tiếp hay không liên tiếp.
- Có tính chất sắp xếp hay không.
- Có trạng thái lặp lại hay không.

## Output của Problem Classifier

Ví dụ schema:

```json
{
  "topic": "dynamic_programming",
  "pattern": "maximum_subarray",
  "confidence": 0.82,
  "key_signals": ["subarray liên tiếp", "tối đa tổng", "mảng số nguyên"],
  "recommended_hint_path": ["input_output", "brute_force", "state_definition", "transition_question"]
}
```
