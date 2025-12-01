# 구조 변경 및 수정 사항

## app.cooking_assistant.domain

### entities
- cooking_state.py
  - 랭그래프 state 이므로 app.cooking_assistant.workflow.state 패키지로 이동
- question.py, recipe.py(오타확인), recommendation.py 는 사용하지 않는 것 같은데, 본래 state에 들어가는 내용으로 생각 됨, state에서 사용할것으로 판단되면 소스 수정 필요함.
- potrs.py
  - llm_port.py 에 인자값 결과 값이 중복되는 함수가 많고 이를 좀더 공통화 시킬수 있게 검토
  - image_port.py 중복되는 함수는 없으나 좀더 범용적으로 변경 가능한지 검토
  - port 패키지는 app.core 에 위치하는 것이 맞음, port는 범용적이고 공통적이어야함
- exceptions.py cooking_assistant 의 root에 위치하는 것이 맞는 것 같은데 타당성 검토필요
  - 그냥 루트가 애매하면 exceptions 이라는 패키지에는 어떨까 타당성 검토

## app.prompts
- 위치가 app.cooking_assistant.prompts 으로 가는 것에 대한 타당성 검토

## core.prompt_loader.py
- Example내용을 범용적으로 변경

# 잘못 정리된 port-dapter
- ports.py는 좀 더 core에 맞게 범용적으로 작성 되어야 함
- app.dapters.* 는 core에 들어가는게 맞는것 같고 범용 적으로 작성 되어야 함
  - core가 아닐수도 있음, cooking_assistant아래 있어야 할 수도 있는 거라서 충분한 검토 필요
  - 이후 prompt = self.prompt_loader.render(...) 라던지 분기처리등 비지니스 로직은 해당 아답터를 호출하는 쪽에서 담당, node나 workflow, service등등 직접 호출하는 쪽에서 담당해야함
  - 순수하게 아답터기능만 있어야함
  - 이를 바탕으로 수정계획을 세운 후 수정이 필요함
- app.dapters.* 는 단순할 필요가 있음, 프롬프트를 받아서 결과만 던지는 형태가 맞지 않나 생각이 듬

# module.py 위치
- 해당 파일은 템플릿에서 쓰는거를 정의하는 파일인데 core에 있음, 클래스명 및 위치에 대한 충분한 고민 및 검토 필요
- 현재위치가 맞다고 생각하더라도 클래스명과 주석은 범용적으로 변경

# 쿠킹어시스턴스에서 잘못 구현된 부분
- base_node.py에서 __call__ > _handle_secondary_intent 할 경우 secondary_intents.pop(0) 하는데 결국 마지막에는 secondary_intents정보가 사라져서 cooking_service에서 secondary_intents 별로 리턴값을 만들어 줘야하는데 해당 부분이 구현이 안되어 있음
  - 예를 들어서 primary_intent가 recommend 이고 secondary_intents 가 [recipe_create, question] 일 경우에 현재는 primary에 해당하는 recommend 값만 response에 담기고 secondary_intents는 담기지 않음, 이게 아니고 recommend, recipe_create, question 전부 동일하게 담겨야함

# 추후 고민해야할부분 (이건 지금 안하는거야, 다고치고 따로 생각해보자)
## workflow(랭체인) 의 edge와 base_node의 관계 및 흐름에 대한 고찰이 필요함
## prompt_loader를 좀 더 편하고 깔끔하게 쓸수있는 방안에 대한 고찰이 필요함

