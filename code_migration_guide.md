# 코드 마이그레이션 가이드

## 1. FastAPI + Pydantic 2.x 대응

### 변경 필요 사항:
```python
# Before (Pydantic 1.x)
from pydantic import BaseModel

class Config:
    orm_mode = True

# After (Pydantic 2.x)
from pydantic import BaseModel, ConfigDict

model_config = ConfigDict(from_attributes=True)
```

## 2. 헬스체크 엔드포인트 추가

### main.py에 추가:
```python
@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }
```

## 3. NeMo 호환성 대응

### 임시 해결책:
```python
# PyTorch 2.x 호환성 강제
import torch
if hasattr(torch, '_C') and hasattr(torch._C, '_set_print_stack_traces_on_fatal_signal'):
    torch._C._set_print_stack_traces_on_fatal_signal(False)
```

## 4. 대체재 고려사항

### Gradio → Streamlit 마이그레이션:
```python
# Gradio
import gradio as gr
interface = gr.Interface(fn=process, inputs='text', outputs='text')

# Streamlit
import streamlit as st
input_text = st.text_input('입력')
if st.button('처리'):
    result = process(input_text)
    st.write(result)
```