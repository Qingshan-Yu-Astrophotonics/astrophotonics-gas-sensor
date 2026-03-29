# Astrophotonics sensor for exoplanetary gas detection

## Part 1 | throughput_sim

用于评估如下天文系统的端到端性能：**1 米级望远镜、无自适应光学（AO）、前端使用 photonic lantern、工作波段 800–1100 nm**。项目重点是建立一个**快速、透明、可扩展的系统级 surrogate model**，用于回答三个核心问题：

1. 在 3 / 7 / 19 port photonic lantern 三种配置下，系统总光子效率大概是多少？
2. 在给定 SNR 阈值下，系统的极限星等是多少？
3. 如果延长总积分时间，极限星等会如何提升？

本 README 将解释项目的设计思想、物理近似、模块结构、关键公式、参数意义、输出内容以及局限性。

---

## 1. 这个项目解决的是什么问题

对于 1 m 级望远镜、无 AO 的场景，望远镜焦面通常是 seeing-limited，而不是 diffraction-limited。此时光进入 photonic lantern 多模端后，不会像单模光纤耦合那样只关心一个基模，而是涉及：

- 多模端到底支持多少空间模式
- 这些模式与 lantern 输出单模端口数是否匹配
- 模式数失配会造成多少吞吐损失
- taper 过渡是否可能引入额外非绝热损耗
- 输出到 3 / 7 / 19 个单模端口后，每个端口的平均通量如何变化
- 这些变化最终会怎样影响天文探测中的 SNR 和极限星等

如果直接上全波电磁仿真，开发成本很高，参数 sweep 很慢，而且在系统方案评估阶段通常不划算。因此，本项目先建立**第一版 surrogate**，把最关键的物理机制保留下来。

---

## 2. 模型分层

整个系统被拆成两层：

### 2.1 外部系统层
这一层处理灯笼外部的整个天文观测链路，包括：

- 望远镜有效 collecting area
- 大气传输
- 镜面反射损耗
- 前端光学透过率
- 灯笼输入端注入效率
- 探测器量子效率 QE
- 天空背景、暗电流、读噪

这一层最终给出一个除 lantern 内部传播之外的系统 throughput 框架。

### 2.2 光子灯笼内部传播层
这一层专门处理已经进入 photonic lantern 多模端后的事情。第一版不求解实际波导中的复振幅场传播，而是把 lantern 看成一个：

- 输入：若干多模端局域模式上的功率分布
- 输出：分配到 N 个单模端口上的功率分布
- 中间：有模式数匹配损失、非绝热损耗、模态混合、端口映射

---

## 3. 第一版物理框架总览

项目的总系统效率写为：

$\[
\eta_{\mathrm{sys}}(\lambda) =
\eta_{\mathrm{atm}}(\lambda)
\eta_{\mathrm{tel}}(\lambda)
\eta_{\mathrm{fore}}(\lambda)
\eta_{\mathrm{inj}}(\lambda)
\eta_{\mathrm{internal}}(\lambda)
QE(\lambda)
\]$

其中：

- \(\eta_{\mathrm{atm}}\)：大气传输
- \(\eta_{\mathrm{tel}}\)：望远镜镜面链路反射率
- \(\eta_{\mathrm{fore}}\)：前端光学透过率
- \(\eta_{\mathrm{inj}}\)：外部注入到 lantern 多模端的效率
- \(\eta_{\mathrm{internal}}\)：lantern 内部传播 surrogate 给出的吞吐
- \(QE\)：探测器量子效率

这个表达式把 lantern 内部传播与系统外部传输清楚地拆开，使得代码更容易维护，也更适合未来升级。

---

## 5. 光源模型：AB 星等到光子通量

### 5.1 为什么选 AB 星等
天文观测里用 AB 星等做第一版源模型非常方便，因为它定义清晰、与波段积分兼容，而且足够适合作为概念验证级别仿真。

### 5.2 基本关系
AB 零点：

- \(F_{\nu,0} = 3631\,\mathrm{Jy}\)

对给定星等 \(m_{AB}\)：

\[
F_\nu = F_{\nu,0} 10^{-0.4 m_{AB}}
\]

然后把每单位频率的能流密度转换为每单位波长上的光子流率，最终统一成：

- photons / s / m² / nm

这样在给定波长网格后，就可以做数值积分：

\[
N_s = t_{\rm exp} A_{\rm eff} \sum_\lambda \Phi_\lambda \, \eta_{\rm sys}(\lambda) \, \Delta\lambda
\]

这里：

- \(N_s\)：源光子计数
- \(A_{\rm eff}\)：望远镜有效 collecting area
- \(t_{\rm exp}\)：曝光时间
- \(\Phi_\lambda\)：光子谱流量

---

## 6. 望远镜有效面积与外部 throughput

### 6.1 有效 collecting area
项目默认使用：

\[
A_{\mathrm{eff}} = \frac{\pi}{4}(D^2 - D_{\mathrm{obs}}^2)
\]

其中：

- \(D\)：主镜口径
- \(D_{\mathrm{obs}}\)：中央遮拦直径

这一步的意义是把镜面尺寸与中央遮拦统一折算为真正用于收集光子的几何面积。

### 6.2 外部 throughput 的角色
在这个项目里，除了 lantern 内部传播之外，其余所有 throughput 都被当作外部效率项，统一以乘法方式组合。这样做并不是说物理上所有过程都完全独立，而是为了第一版模型在工程上足够清晰：

- 哪些参数来自望远镜本体
- 哪些参数来自光学链路
- 哪些参数来自灯笼内部
- 哪些参数来自探测器

---

## 7. Photonic Lantern 内部传播 surrogate 的核心思想

这是整个项目最关键的部分。

### 7.1 为什么不用全场传播
如果直接求灯笼内部场传播，需要显式处理：

- 波导横向折射率分布
- taper 几何
- 模式本征值与传播常数
- 模间耦合
- 波长依赖
- 输出端口场分布

这在器件设计阶段很有价值，但在系统级第一版仿真里会把问题复杂化。当前最重要的是先建立一个可以回答“值不值得继续”的模型，因此选择把 lantern 内部传播压缩成**功率传输 surrogate**。

### 7.2 surrogate 的输入与输出
内部模型输入：

- 多模端模式功率向量 \(\mathbf{p}_{\rm in}\)

内部模型输出：

- N 个单模端口上的输出功率向量 \(\mathbf{p}_{\rm out}\)
- 该波长下的总内部 throughput \(\eta_{\rm internal}(\lambda)\)

这就足够支持：

- 算 band-averaged throughput
- 算端口通量分布
- 把 throughput 继续送入系统 SNR 和极限星等模块

---

## 8. surrogate 的四个组成部分

内部传播 surrogate 被写成四个连续模块：

\[
\mathbf{p}_{\rm out}(\lambda)=
\eta_{\rm par}(\lambda)
\mathbf{R}(\lambda)
\mathbf{K}(\lambda)
\mathbf{S}_{\rm match}(\lambda)
\mathbf{p}_{\rm in}(\lambda)
\]

下面分别解释。

### 8.1 模式数匹配：\(\mathbf{S}_{\rm match}\)
第一版最重要的物理约束就是：多模端支持的模式数不能比输出端口可承载的总自由度多太多，否则必然有损耗。

项目中使用经验表达式：

\[
M_{\rm mm}(\lambda)=N_{\rm port}\left(\frac{\lambda_0}{\lambda}\right)^2
\]

意思是：在设计波长 \(\lambda_0\) 处，lantern 的多模端支持模式数与端口数大致匹配；往更短波长走，由于归一化频率增大，多模端支持模式数增加。

于是定义模式匹配 throughput：

\[
\eta_{\rm match}(\lambda)=
\min\left(1,\frac{N_{\rm port}}{M_{\rm mm}(\lambda)}\right)
\]

这是本版本中最关键的损失机制。

### 8.2 非绝热惩罚：\(\eta_{\rm ad}\)
即便模式数大致匹配，真实 taper 过渡仍可能因为不够平滑而引入额外损失。第一版不显式求解 taper 中的局域本征模演化，而用一个经验罚函数表示：

\[
\eta_{\rm ad}(\lambda)= \exp\left[-\alpha_{\rm ad}\max\left(0, \frac{M_{\rm mm}(\lambda)}{N_{\rm port}} - 1\right)\right]
\]

这里：

- \(\alpha_{\rm ad}\) 越大，说明系统对模式过多更加敏感
- 当短波端模式数增长时，该项会压低 throughput

### 8.3 模态混合：\(\mathbf{K}\)
真实 lantern 内部不会简单地保持每个输入模式绝对独立。不同模式在 taper 中可能发生一定程度的混合。第一版中使用高斯核矩阵构造模态混合：

\[
K_{ij} \propto \exp\left[-\frac{(i-j)^2}{2\sigma_{\rm mix}^2}\right]
\]

并对每一列归一化。其含义是：

- \(\sigma_{\rm mix}\) 很小时，混合弱，接近“各模式独立跟随”
- \(\sigma_{\rm mix}\) 较大时，模式间功率更容易重分配

### 8.4 端口映射：\(\mathbf{R}\)
最后一步是把 surviving mode power 映射到 N 个端口。第一版至少支持两种方式：

1. `uniform_port_map`：平均分到各端口
2. `random_fixed_port_map`：使用固定随机列归一矩阵，模拟现实器件中的端口不均匀性

这样做的目的是：

- 一方面提供简单、稳健的默认近似
- 另一方面也能在不做全波仿真的情况下，粗略反映端口间不均匀分光的可能性

---

## 9. 总内部 throughput 的定义

第一版中，寄生损耗项先设为常数：

\[
\eta_{\rm par}(\lambda)=\eta_0
\]

因此总内部 throughput 为：

\[
\eta_{\rm internal}(\lambda)=
\eta_{\rm par}(\lambda)
\eta_{\rm match}(\lambda)
\eta_{\rm ad}(\lambda)
\]

它代表 lantern 内部真正存活并输出到单模端口的总功率比例。后续的端口功率分配只是在这部分 surviving power 上继续分配。

---

## 10. 为什么模式数会有波长依赖

这是理解本项目的关键。

多模波导支持模式数与归一化频率 \(V\) 的平方近似成正比，而 \(V\) 又与 \(1/\lambda\) 成正比。所以：

\[
M \propto \lambda^{-2}
\]

这意味着：

- 对同一个 lantern 设计，短波端会支持更多模式
- 因此短波端更容易发生模式数失配
- 结果是内部 throughput 往往在短波端更差

所以本项目里，最重要的光谱结构之一，就是 `eta_internal(lambda)` 在 800–1100 nm 之间的变化。这种变化不是后端探测器造成的，而首先是 lantern 自身模式数与波长关系造成的。

---

## 11. 天空背景与噪声模型

为了把 throughput 结果转化成观测能力，需要把噪声带进来。

### 11.1 背景模型
第一版支持：

- 常数天空背景
- 或用户提供随波长变化的数组

单位统一为：

- photons / s / m² / nm / arcsec²

背景计数写为：

\[
N_{\rm sky}= t_{\rm exp} A_{\rm eff} \Omega_{\rm ap}
\sum_\lambda \Phi_{\rm sky,\lambda}\eta_{\rm sys}(\lambda)\Delta\lambda
\]

其中 \(\Omega_{\rm ap}\) 表示观测 aperture 对应的天空立体角，单位通常以 arcsec² 表示。

### 11.2 暗电流与读噪
暗电流与读噪分别表示：

- 探测器每像素每秒产生的暗电流电子数
- 读出时每像素附加的随机噪声

在多端口输出场景下，这一块尤其重要，因为更多端口在实际系统中往往意味着更多像素参与读出，从而可能在 read-noise-limited 条件下抵消掉部分 throughput 增益。

---

## 12. SNR 的定义

项目使用标准的计数型 SNR 公式：

\[
\mathrm{SNR} = \frac{N_s}{\sqrt{N_s + N_{\rm sky} + N_{\rm dark} + n_{\rm pix}RN^2}}
\]

其中：

- \(N_s\)：源计数
- \(N_{\rm sky}\)：背景计数
- \(N_{\rm dark}\)：暗电流计数
- \(RN\)：每像素读噪
- \(n_{\rm pix}\)：参与读出的像素数

这是把系统 throughput 和真实观测能力连接起来的桥梁。

---

## 13. 极限星等的定义与求解

### 13.1 什么是极限星等
极限星等 \(m_{\rm lim}\) 是指：在给定总积分时间和目标 SNR 下，能刚好达到该 SNR 阈值的最暗源的星等。

### 13.2 数值求解方式
项目会对函数：

\[
SNR(m_{AB}) - SNR_{\rm target}
\]

做 root finding，找到解：

\[
SNR(m_{\rm lim}) = SNR_{\rm target}
\]

实现上建议使用 `scipy.optimize.brentq`，因为它稳定、易诊断、适合一维单峰型问题。

---

## 14. 为什么还要画 m_lim vs total time

因为只看单一曝光时间往往不足以评估系统有没有潜力。真实观测会关心：

- 如果总曝光时间增加 10 倍，极限星等能提升多少？
- 3 / 7 / 19 port 哪个在长积分下收益更大？
- throughput 的增益会不会在读噪主导时被更多像素数抵消？

所以项目会对多组总积分时间扫参，输出 `m_lim vs t_total` 曲线。这条曲线是系统设计时非常关键的决策图。

---

## 15. 软件结构设计

项目采用模块化结构，核心目录如下：

```text
lantern_sim/
├─ README.md
├─ requirements.txt
├─ run_sim.py
├─ config/
├─ results/
├─ notebooks/
└─ src/
```

### 15.1 `src/constants.py`
存放物理常数，例如：

- 普朗克常数
- 光速
- Jy 到 SI 单位换算

### 15.2 `src/config_loader.py`
负责读取 yaml 配置文件并合并为统一配置字典。

### 15.3 `src/source_flux.py`
负责：

- AB 星等转 \(F_\nu\)
- \(F_\nu\) 转 photon flux
- 输出统一单位的谱光子流率

### 15.4 `src/telescope.py`
负责：

- collecting area
- 镜面链路 throughput

### 15.5 `src/detector.py`
负责 QE、暗电流、读噪等探测器参数。

### 15.6 `src/sky_background.py`
负责生成和读取天空背景模型。

### 15.7 `src/lantern_surrogate.py`
这是本项目核心模块，实现：

- `mm_mode_count`
- `eta_match`
- `eta_ad`
- `eta_internal`
- 输入模式生成
- 模态混合矩阵
- 端口映射矩阵
- 输出端口功率计算

### 15.8 `src/system_model.py`
负责把所有 throughput 组合成 `eta_sys(lambda)`。

### 15.9 `src/snr.py`
负责：

- 源计数
- 背景计数
- 暗计数
- SNR 计算

### 15.10 `src/limiting_mag.py`
负责极限星等求解与积分时间 sweep。

### 15.11 `src/plots.py`
负责所有图的输出。

### 15.12 `src/sweep.py`
负责批量扫 port 数、时间、lantern 参数，并汇总表格。

---

## 16. 配置文件设计原则

所有关键参数都放在 `yaml` 中，而不是散落在代码里。原因有三个：

1. 更容易做参数 sweep
2. 更容易和 code agent / notebook 对接
3. 将来替换更复杂的 lantern model 时，接口不需要大改

建议配置拆分为：

- `base.yaml`：全局设置
- `telescope_1m.yaml`：望远镜与光学链路
- `detector.yaml`：探测器
- `scenarios.yaml`：不同 port 与仿真场景

---

## 17. 输出图的物理意义

项目默认应生成以下关键图。

### 17.1 `mode_count_vs_lambda.png`
展示 `M_mm(lambda)` 随波长变化。它能直接告诉使用者：短波端为何更容易发生模式过多、造成模式失配。

### 17.2 `eta_internal_vs_lambda.png`
展示 lantern 内部 throughput 的光谱结构。它反映的是内部器件本身，而不是外部望远镜或探测器。

### 17.3 `eta_sys_vs_lambda.png`
展示完整系统 throughput。它将 lantern 内部吞吐与大气、镜面、前端、探测器一起纳入。

### 17.4 `snr_vs_mag.png`
展示给定曝光条件下，源越暗时 SNR 如何下降，以及不同 port 数谁更有优势。

### 17.5 `m_lim_vs_time.png`
展示延长总积分时间后极限星等如何变深。这是做方案比较时最关键的一张图之一。

### 17.6 `port_power_distribution_example.png`
展示某个代表波长下，多端口输出功率分布是否均匀，有没有端口间明显偏差。

---

## 18. 默认参数的角色

README 中给出的默认参数不是“真实系统最终数值”，而是为了让第一版项目能顺利跑通，并且数量级合理。用户应根据自己的系统逐步替换：

- 望远镜结构参数
- 前端光学效率
- 探测器 QE / 暗噪 / 读噪
- lantern 的设计波长和内部损耗先验
- 有效天空背景

因此，**本项目更像一个可替换、可校准的框架**，而不是某个特定仪器的最终权威模型。

---

## 19. 自检与 sanity checks

项目实现后应至少做以下 sanity checks：

1. `eta_internal(lambda)` 始终位于 `[0, 1]`
2. 输出端口功率和不应超过内部 throughput
3. 源越亮，SNR 必须越高
4. 总积分时间增加时，极限星等不应变浅
5. 若提高总 throughput，则极限星等应更深

这些检查不是形式主义，而是为了尽早发现单位错误、数组广播错误和归一化错误。

---

## 20. 本模型的主要局限性

必须明确：本项目是第一版 surrogate，因此有明显边界。

### 20.1 未显式建模实际波导几何
项目没有输入纤芯排布、折射率剖面、taper 长度、几何误差等真实器件参数，因此不能替代真正的 photonic lantern 器件设计仿真。

### 20.2 模态混合是经验模型
高斯核混合矩阵只是一个可解释、可调的经验 surrogate，并不等同于某个具体器件的真实 mode coupling matrix。

### 20.3 注入效率仍被外部参数化
本版本把注入到 lantern 多模端的效率 `eta_inj` 单独参数化，而没有从 seeing PSF、焦比、NA 和 mode field overlap 开始严格推导。

### 20.4 天空背景与探测器模型较简化
真实系统可能涉及更复杂的背景结构、谱仪格式、像元映射和波长依赖读噪，这些在本版本中还没有展开。

### 20.5 极限星等结果是“系统级第一版估算”
因此它适合用于：

- 方案比较
- 参数敏感性分析
- 判断 3 / 7 / 19 port 哪个更值得继续做

但不应直接当作最终 instrument requirement 文档中的唯一依据。

---

## 22. 后续升级路线

这个项目的自然升级路径如下：

### 22.1 第二版：改进外部注入效率
加入 seeing PSF、焦比、数值孔径、纤芯接受锥等模型，把 `eta_inj` 从常数升级为波长与 seeing 相关函数。

### 22.2 第三版：接入 `cbeam`
让 lantern 内部 propagation 由耦合模理论求出的 transfer matrix 替代 surrogate 的部分模块。

### 22.3 第四版：接入 `lightbeam`
对少数候选结构做更高保真的 BPM cross-check，用于验证 `cbeam` 或 surrogate 的趋势是否合理。

### 22.4 第五版：接近真实仪器
加入：

- 实测 throughput 曲线
- 实测探测器 QE
- 实测背景
- 实测端口间不均匀性
- 更接近实际的 spectrograph pixel budget

---