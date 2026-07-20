from poussins import Lemma, Prop, Environment
from poussins.ast.expr import ESort, EVar  # 💡 EVar も追加
from poussins.ast.universe import UnivLevelSucc, UnivLevelZero
# 💡 あなたの実装したConstantDeclarationをインポート
from poussins.environment import ConstantDeclaration 

env = Environment()

# A, B, C は型（Sort 1）であるという定数を登録する
type_sort = ESort(UnivLevelSucc(UnivLevelZero()))  # Type

# あなたの ConstantDeclaration に完全準拠。
# 値（value）が必須の場合は、自身を返す、あるいは定数としての表現をセットします。
env.add(ConstantDeclaration(name="A", level_params=(), type=type_sort, value=EVar("A")))
env.add(ConstantDeclaration(name="B", level_params=(), type=type_sort, value=EVar("B")))
env.add(ConstantDeclaration(name="C", level_params=(), type=type_sort, value=EVar("C")))

# 2. Prop DSLを定義（中身は EVar("A") などのまま）
a, b, c = Prop("A"), Prop("B"), Prop("C")

# 3. 定理（Lemma）の初期化。★上で A, B, C を登録した `env` を引数に渡す！
hilbert_s = Lemma("HilbertS", ((a >> (b >> c)) >> ((a >> b) >> (a >> c))), env)
print(f"{hilbert_s.name}: {hilbert_s.statement}")

# 4. タクティクスを実行
hilbert_s.intro("habc")
hilbert_s.intro("hab")
hilbert_s.intro("ha")
hilbert_s.apply("habc")
hilbert_s.exact("ha")
hilbert_s.apply("hab")
hilbert_s.exact("ha")

# 5. 最後に証明をクローズ（登録用の環境を渡す）
hilbert_s.qed(env)