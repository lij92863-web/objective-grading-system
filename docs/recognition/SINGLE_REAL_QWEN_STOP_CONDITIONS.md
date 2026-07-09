# Single Real Qwen Stop Conditions (R388)

遇到以下任一情况立即停止：

1. 图片非匿名
2. ROI 缺失
3. identity ROI 缺失
4. check-only 未通过
5. API key 缺失
6. output path 不在 data/tmp
7. save_raw_response=true
8. emit_base64=true
9. max_calls > 1
10. parser 出现 malformed_response
11. parser 出现 unexpected_question_id
12. parser 出现 identity_conflict
13. 任何结果试图进入 grade_all
14. 任何结果试图生成正式报告
