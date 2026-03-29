# Config 说明

本文档说明 `config/` 目录下所有 `.yaml` 文件中变量的物理含义、单位和它们在模型中的作用。目标是让你在调参时知道每个量对应的是哪一段物理链路，以及它最终会影响 `eta_internal(lambda)`、`eta_sys(lambda)`、SNR 还是极限星等 `m_lim`。

## 总体关系

本项目的端到端系统吞吐定义为：

```text
eta_sys(lambda) = eta_atm(lambda)
                  * eta_tel(lambda)
                  * eta_fore(lambda)
                  * eta_inj(lambda)
                  * eta_internal(lambda)
                  * QE(lambda)
```

其中：

- `eta_atm`、`eta_tel`、`eta_fore`、`eta_inj` 来自外部系统配置。
- `eta_internal` 来自 photonic lantern surrogate 配置。
- `QE`、暗电流、读噪、像元数来自探测器配置。

## 1. `base.yaml`

[`base.yaml`](/d:/GitRepos/astrophotonics-gas-sensor/config/base.yaml) 定义全局控制参数，包括波长网格、目标 SNR、光源与观测设置、天空背景和 lantern 默认参数。

### `wavelength_nm`

#### `start_nm`

- 含义：仿真的起始波长。
- 单位：nm。
- 物理作用：确定计算波段的短波端。
- 影响：会改变积分波段、模式数曲线、throughput 曲线以及最后的源计数和背景计数。

#### `stop_nm`

- 含义：仿真的终止波长。
- 单位：nm。
- 物理作用：确定计算波段的长波端。
- 影响：与 `start_nm` 一起决定系统积分带宽。

#### `step_nm`

- 含义：离散波长网格的采样步长。
- 单位：nm。
- 物理作用：决定数值积分和绘图的采样精度。
- 影响：步长越小，积分更平滑，但计算量更大。

### `outputs`

#### `figures_dir`

- 含义：PNG 图像输出目录。
- 单位：无。
- 作用：控制 `run_sim.py` 将所有图保存到哪里。

#### `tables_dir`

- 含义：CSV 表格输出目录。
- 单位：无。
- 作用：控制汇总结果表保存位置。

### `snr_target`

- 含义：求解极限星等时要求达到的目标信噪比阈值。
- 单位：无量纲。
- 物理作用：定义“可检测”的最低标准。
- 影响：阈值越高，求出的 `m_lim` 越亮；阈值越低，`m_lim` 越深。

### `default_ports`

- 含义：默认需要扫的 lantern 输出端口数列表。
- 单位：端口个数。
- 物理作用：对应不同 photonic lantern 设计方案，例如 3 / 7 / 19 ports。
- 影响：主要用于 sweep 和绘图分组，本身不直接参与公式计算；实际计算以 `scenarios.yaml` 中的场景为准。

### `source`

#### `root_bracket_mag`

- 含义：极限星等求根时给定的星等搜索区间。
- 单位：AB magnitude。
- 物理作用：为数值 root finder 提供一个包络区间。
- 影响：区间太窄可能找不到解；区间足够大则更稳健。

#### `default_m_ab`

- 含义：默认的 AB 星等，用于示例或快速单点评估。
- 单位：AB magnitude。
- 物理作用：代表默认的目标源亮度。

#### `m_ab_grid.start_mag`

- 含义：绘制 `SNR vs magnitude` 时的起始星等。
- 单位：AB magnitude。

#### `m_ab_grid.stop_mag`

- 含义：绘制 `SNR vs magnitude` 时的终止星等。
- 单位：AB magnitude。

#### `m_ab_grid.step_mag`

- 含义：绘制 `SNR vs magnitude` 时的星等采样步长。
- 单位：AB magnitude。
- 影响：控制 `snr_vs_mag.png` 的分辨率。

### `observation`

#### `exposure_time_s`

- 含义：单次曝光时间。
- 单位：s。
- 物理作用：决定总积分被分成多少次曝光，即 `n_exp = ceil(t_total_s / exposure_time_s)`。
- 影响：在固定总积分时间下，单次曝光越短，叠加次数越多，读噪项累计越重。

#### `target_total_time_s`

- 含义：默认用于报告单个 `m_lim` 的总积分时间。
- 单位：s。
- 物理作用：定义命令行运行时终端摘要里显示的那个代表性观测时长。

#### `t_total_s`

- 含义：用于 sweep 的总积分时间列表。
- 单位：s。
- 物理作用：用于生成 `m_lim_vs_time.png` 和极限星等汇总表。
- 影响：时间越长，源计数和背景计数都增加，通常 `m_lim` 会变深。

### `sky`

#### `model`

- 含义：天空背景模型类型。
- 当前支持：`constant`。
- 物理作用：决定背景光在波段内如何分布。

#### `value_photons_s_m2_nm_arcsec2`

- 含义：天空背景光子的谱面亮度。
- 单位：photons / s / m^2 / nm / arcsec^2。
- 物理作用：表示单位口径面积、单位波长、单位天空面积上的背景光子流。
- 影响：越高则背景噪声越大，SNR 越低，`m_lim` 越浅。

### `lantern`

这一组参数是 photonic lantern surrogate 的默认参数，会被 `scenarios.yaml` 中的场景参数覆盖。

#### `lambda0_nm`

- 含义：lantern 的设计匹配波长。
- 单位：nm。
- 物理作用：在该波长附近，多模端支持模式数与输出端口数最接近匹配。
- 影响：会平移 `eta_match(lambda)` 和 `eta_internal(lambda)` 的转折位置。

#### `alpha_ad`

- 含义：非绝热损耗强度系数。
- 单位：无量纲。
- 物理作用：描述 taper 过渡对模式数过剩的敏感程度。
- 影响：越大表示一旦模式过多，throughput 惩罚越强。

#### `eta0`

- 含义：与波长无关的寄生透过率常数。
- 单位：无量纲，取值应在 `[0, 1]`。
- 物理作用：把吸收、散射、界面损失等一阶寄生损耗压缩成一个常数因子。
- 影响：越大则 `eta_internal` 整体上抬升。

#### `sigma_mix`

- 含义：模式混合高斯核的宽度参数。
- 单位：模式索引空间中的无量纲宽度。
- 物理作用：描述不同模式之间发生功率重分配的强弱。
- 影响：主要改变端口间功率分布，不直接显著改变总 throughput。

#### `w_cut`

- 含义：软截断掩膜的过渡宽度。
- 单位：模式索引空间中的无量纲宽度。
- 物理作用：决定输入模式在接近端口数上限时，是急剧截断还是平滑衰减。
- 影响：越小越接近硬截断，越大则更平滑。

#### `input_profile`

- 含义：输入模式功率分布的默认形式。
- 当前支持：`uniform`、`exponential`。
- 物理作用：决定多模端各阶模式被激发时的相对权重。

#### `port_map_mode`

- 含义：模式功率映射到输出端口时的默认规则。
- 当前支持：`uniform`、`random_fixed`。
- 物理作用：控制 surviving power 如何在各端口之间分配。

#### `random_seed`

- 含义：随机端口映射的随机数种子。
- 单位：无。
- 作用：保证 `random_fixed` 模式下结果可复现。

#### `port_distribution_lambda_nm`

- 含义：用于示例端口功率分布图的代表性波长。
- 单位：nm。
- 作用：控制 `port_power_distribution_example.png` 在哪个波长切片上取样。

## 2. `telescope_1m.yaml`

[`telescope_1m.yaml`](/d:/GitRepos/astrophotonics-gas-sensor/config/telescope_1m.yaml) 描述望远镜与前端光学链路的参数。

### `D_m`

- 含义：主镜口径。
- 单位：m。
- 物理作用：决定收光面积的主尺度。
- 影响：越大则 `A_eff` 越大，源和背景计数都会增加。

### `D_obs_m`

- 含义：中央遮拦直径。
- 单位：m。
- 物理作用：描述次镜或支撑结构造成的遮挡。
- 影响：越大则有效 collecting area 越小。

### `n_mirrors`

- 含义：进入前端之前经过的反射镜数量。
- 单位：个数。
- 物理作用：参与镜面反射率连乘。
- 影响：镜子越多，`eta_tel = mirror_reflectivity ^ n_mirrors` 越低。

### `mirror_reflectivity`

- 含义：单个反射镜的平均反射率。
- 单位：无量纲，取值应在 `[0, 1]`。
- 物理作用：描述每次反射带来的能量保留比例。

### `eta_atm`

- 含义：大气透过率。
- 单位：无量纲。
- 物理作用：概括大气吸收和散射造成的整体透过损失。
- 影响：越低则端到端吞吐越低。

### `eta_fore`

- 含义：前端光学链路透过率。
- 单位：无量纲。
- 物理作用：描述进入 lantern 之前，透镜、窗口、分光元件等前端光学的总透过率。

### `eta_inj`

- 含义：外部系统到 lantern 多模端的注入效率。
- 单位：无量纲。
- 物理作用：描述 seeing-limited 焦斑、对准误差、NA 不匹配等导致的耦合损失。
- 影响：是端到端吞吐里的一个强乘法因子，通常对 `m_lim` 很敏感。

### `seeing_arcsec`

- 含义：视宁度的典型角尺度。
- 单位：arcsec。
- 物理作用：表示大气湍流引起的星像扩展程度。
- 当前状态：在当前版本中主要作为保留参数，还没有显式进入 `eta_inj` 模型。

### `omega_ap_arcsec2`

- 含义：有效采样孔径对应的天空面积。
- 单位：arcsec^2。
- 物理作用：用于把天空背景谱面亮度转换为背景总计数。
- 影响：越大则采集到的背景越多。

## 3. `detector.yaml`

[`detector.yaml`](/d:/GitRepos/astrophotonics-gas-sensor/config/detector.yaml) 描述探测器量子效率与噪声参数。

### `qe`

- 含义：探测器量子效率。
- 单位：无量纲，取值应在 `[0, 1]`。
- 物理作用：表示到达探测器的光子中有多少转化为有效电子计数。
- 影响：是 `eta_sys` 的末端乘法因子。
- 备注：当前可以设为常数；如果将来扩展，也可以改成随波长变化的数组。

### `dark_current_e_s_pix`

- 含义：暗电流。
- 单位：electrons / s / pixel。
- 物理作用：表示在无光情况下每个像元每秒产生的热电子数。
- 影响：总暗计数 `N_dark = dark_current * t_total * n_pix`。

### `read_noise_e_pix`

- 含义：单像元读出噪声。
- 单位：electrons / pixel / read。
- 物理作用：表示每次读出时电子学引入的随机噪声。
- 影响：在 SNR 里以 `n_exp * n_pix * RN^2` 进入方差项。

### `n_pix`

- 含义：一次提取信号时参与读出的等效像元数。
- 单位：pixel。
- 物理作用：代表光谱提取 aperture 或多端口汇总后所占用的探测器像元预算。
- 影响：越大则暗电流与读噪都更高。
- 备注：当前版本中 `n_pix` 对不同 port 场景相同，因此还没有显式体现“端口越多，像元数可能越多”的效应。

## 4. `scenarios.yaml`

[`scenarios.yaml`](/d:/GitRepos/astrophotonics-gas-sensor/config/scenarios.yaml) 定义实际运行的 sweep 场景。每个场景表示一种 lantern 设计或一种参数组合。

### `scenarios`

- 含义：场景列表。
- 作用：`run_sim.py` 会按顺序逐个运行这些场景，并在图表中进行比较。

### 对于每个场景

#### `name`

- 含义：场景名称。
- 作用：用于终端日志、CSV 表和图例标签。

#### `n_port`

- 含义：lantern 输出单模端口数量。
- 单位：个数。
- 物理作用：表示 photonic lantern 将 surviving power 分到多少个单模输出通道。
- 影响：会影响模式数匹配、内部吞吐和端口功率分配。

#### `lantern.alpha_ad`

- 含义：该场景覆盖默认 `alpha_ad` 的值。
- 作用：允许不同端口数采用不同非绝热损耗假设。

#### `lantern.sigma_mix`

- 含义：该场景覆盖默认 `sigma_mix` 的值。
- 作用：允许不同器件结构有不同模式混合强度。

#### `lantern.eta0`

- 含义：该场景覆盖默认 `eta0` 的值。
- 作用：允许不同器件结构有不同寄生透过率。

#### `lantern.w_cut`

- 含义：该场景覆盖默认 `w_cut` 的值。
- 作用：允许不同器件设计采用不同的软截断过渡宽度。

## 调参建议

如果你的目标是做物理上更有区分度的 3 / 7 / 19-port 比较，优先考虑以下配置项：

- `eta_inj`：决定外部耦合损失，是强影响项。
- `n_pix`：决定多端口读出代价是否进入 SNR。
- `alpha_ad`、`eta0`：决定 lantern 内部总吞吐差异。
- `lambda0_nm`：决定 throughput 曲线的波段匹配位置。
- `omega_ap_arcsec2` 与天空背景：决定背景受限程度。

如果只是想调整图像采样或 sweep 范围，则优先改：

- `wavelength_nm`
- `source.m_ab_grid`
- `observation.t_total_s`
- `outputs.figures_dir`
- `outputs.tables_dir`
