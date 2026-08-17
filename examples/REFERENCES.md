# Structural references for the example gallery

The generated figures are explanatory schematics, not reproductions of the
published figures and not process-qualified layouts. Dimensions are chosen for
legibility. The references below provide the device archetypes and terminology
used by the scripts.

## Supplied-image provenance

| Supplied reference | Publication source |
|---|---|
| Labeled HBM stack beside a GPU | Hanwha, “Powering AI: Advanced semiconductor manufacturing solutions” (2024), [source page](https://www.hanwha.com/newsroom/news/feature-stories/powering-ai-semiconductor-manufacturing-solutions.do). |
| Signal layers / power / nTSV rendering | Aminext, “What is Backside Power Delivery (BSP)? Redefining the Chip Power Map for the 2nm Revolution,” [source page](https://www.aminext.blog/en/post/backside-power-delivery-bsp-explained-1). |
| Simplified backside-power illustration (exploded orange signal plates, gray power block with an nTSV, solder balls, dark background) | Stylized 3D render from AmiNext, "What is Backside Power Delivery (BSP)? Redefining the Chip Power Map for the 2nm Revolution," [source page](https://www.aminext.blog/en/post/backside-power-delivery-bsp-explained-1), the same article as the nTSV rendering above. Used only for the block composition, viewpoint and the signal-layers / power / nTSV callouts (`fig_backside_power_simple.py`), and the geometry, dimensions and colors are new. |
| Top-down photograph of an H100 GPU package with the package substrate, interposer, GPU die and six HBM sites outlined, and an exploded CoWoS illustration (substrate, interposer, SoC, HBM) | Both were supplied as screenshots from "TSMC 'Super Carrier' CoWoS interposer gets bigger, enabling massive AI chips to reach 9-reticle sizes with 12 HBM4 stacks," *Tom's Hardware*, [article](https://www.tomshardware.com/tech-industry/tsmc-super-carrier-cowos-interposer-gets-bigger-enabling-massive-ai-chips-to-reach-9-reticle-sizes-with-12-hbm4-stacks). The photograph carries a SemiAnalysis watermark. Used only for the die arrangement, exploded composition, viewpoint and callout set (`fig_gpu_cowos_exploded.py` and `fig_gpu_cowos_assembled.py`), and the geometry, dimensions and colors are new. |
| Planar / FinFET / GAAFET / CFET evolution diagram (green gate, blue PMOS, red NMOS, pink well, gray isolation) | Widely circulated evolution diagram. Supplied from a LinkedIn post by Kumar Priyadarshi, "4 stages of evolution of transistors" (2024), [post](https://www.linkedin.com/posts/kumar-priyadarshi-b0a2a7a2_4-stages-of-evolution-of-transistors-1-activity-7263400584328708097-B6sk), as a screenshot that also carries a Zhihu watermark ("@Tommy哥"). Neither posting credits a creator, so the diagram is older than both and its author has not been identified. Only its color-by-role scheme is followed (`fig_transistor_evolution_rolecolor.py`). |
| NEO Semiconductor "3D DRAM" concept slide (gray capacitors, blue word lines/transistors, teal channel and bit line, dark background) | NEO Semiconductor 3D X-DRAM material (see the brochure below); the slide's presentation scheme is followed in `fig_dram3d_reference_colors.py`. |
| Two-panel 3D DRAM capacitor schematic (vertical capacitors on a bit-line array, and a staircase bit-line with horizontal capacitors, in red, green and white) | A generic capacitor-architecture comparison of the kind that appears widely in 3D DRAM presentations. Only its role-color scheme and panel composition are followed (`fig_dram3d_capacitor_schematics.py`). |
| 3D X-DRAM array screenshot | M. Tyson, “3D X-DRAM Roadmap: 1Tb Die Density by 2030,” *Tom's Hardware* (4 May 2023), where the image is credited to NEO Semiconductor, [article](https://www.tomshardware.com/news/3d-x-dram-roadmap-1tb-die-density-by-2030); NEO Semiconductor, [official 3D X-DRAM brochure](https://neosemic.com/wp-content/uploads/2023/07/X-Dram3d_Br.pdf). |

No reference image is redistributed by this package, and none is reproduced
by a generated figure. Each script builds new schematic geometry from the
concept, so a supplied image contributes composition, viewpoint and the set
of callouts and nothing else. Where a publisher is named above, the naming
is attribution rather than a claim of permission. If you recognize an
unidentified image, please open an issue and it will be credited or the
figure withdrawn.

Three figures carry a reference's own role or presentation colors. They are
there to demonstrate that both renderers accept an explicit color override,
so the scheme is the subject of the demonstration rather than an attempt to
reproduce the original artwork. Each is kept in its own script, the palette
remains the default everywhere else, and removing the override returns any
of them to material coloring.

## Logic and interconnect

| Example concept | Reference |
|---|---|
| Self-aligned double-gate FinFET | D. Hisamoto et al., “FinFET—A self-aligned double-gate MOSFET scalable to 20 nm,” *IEEE Transactions on Electron Devices* 47, 2320–2325 (2000), [doi:10.1109/16.887014](https://doi.org/10.1109/16.887014). |
| Stacked gate-all-around nanosheets | N. Loubet et al., “Stacked nanosheet gate-all-around transistor to enable scaling beyond FinFET,” *Symposium on VLSI Technology* (2017), [doi:10.23919/VLSIT.2017.7998183](https://doi.org/10.23919/VLSIT.2017.7998183). |
| Buried rails and backside power | D. Prasad et al., “Buried Power Rails and Back-side Power Grids: Arm CPU Power Delivery Network Design Beyond 5nm,” *IEDM* (2019), [doi:10.1109/IEDM19573.2019.8993617](https://doi.org/10.1109/IEDM19573.2019.8993617). |
| nTSVs landing on buried rails | A. Veloso et al., “Scaled FinFETs Connected by Using Both Wafer Sides for Routing via Buried Power Rails,” *IEEE Transactions on Electron Devices* 69, 7173–7179 (2022), [doi:10.1109/TED.2022.3205561](https://doi.org/10.1109/TED.2022.3205561). |

## Memory

| Example concept | Reference |
|---|---|
| One-transistor/one-capacitor DRAM | R. H. Dennard, “Field-Effect Transistor Memory,” US Patent 3,387,286 (1968), [Google Patents](https://patents.google.com/patent/US3387286A/en). |
| DRAM scaling and trench/stacked capacitors | J. A. Mandelman et al., “Challenges and future directions for the scaling of dynamic random-access memory,” *IBM Journal of Research and Development* 46, 187–212 (2002), [doi:10.1147/rd.462.0187](https://doi.org/10.1147/rd.462.0187). |
| Bit-cost-scalable 3D NAND | H. Tanaka et al., “Bit Cost Scalable Technology with Punch and Plug Process for Ultra High Density Flash Memory,” *Symposium on VLSI Technology* (2007), [doi:10.1109/VLSIT.2007.4339708](https://doi.org/10.1109/VLSIT.2007.4339708). |
| Vertical-bit-line 3D DRAM | J. Park et al., “A Three Dimensional DRAM (3D DRAM) Technology for the Next Decades,” *IEEE Symposium on VLSI Technology and Circuits* (2024), [doi:10.1109/VLSITechnologyandCir46783.2024.10631471](https://doi.org/10.1109/VLSITechnologyandCir46783.2024.10631471). |

## Lasers and LEDs

| Example concept | Reference |
|---|---|
| GaAs junction laser | R. N. Hall et al., “Coherent Light Emission From GaAs Junctions,” *Physical Review Letters* 9, 366 (1962), [doi:10.1103/PhysRevLett.9.366](https://doi.org/10.1103/PhysRevLett.9.366). |
| Room-temperature double-heterostructure laser | I. Hayashi et al., “Junction Lasers Which Operate Continuously at Room Temperature,” *Applied Physics Letters* 17, 109–111 (1970), [doi:10.1063/1.1653326](https://doi.org/10.1063/1.1653326). |
| Distributed-feedback laser principle | H. Kogelnik and C. V. Shank, “Stimulated Emission in a Periodic Structure,” *Applied Physics Letters* 18, 152–154 (1971), [doi:10.1063/1.1653605](https://doi.org/10.1063/1.1653605). |
| Surface-emitting injection laser | H. Soda et al., “GaInAsP/InP Surface Emitting Injection Lasers,” *Japanese Journal of Applied Physics* 18, 2329–2330 (1979), [doi:10.1143/JJAP.18.2329](https://doi.org/10.1143/JJAP.18.2329). |
| High-brightness InGaN/AlGaN blue LED | S. Nakamura, T. Mukai and M. Senoh, “Candela-class high-brightness InGaN/AlGaN double-heterostructure blue-light-emitting diodes,” *Applied Physics Letters* 64, 1687–1689 (1994), [doi:10.1063/1.111832](https://doi.org/10.1063/1.111832). |
| InGaN/GaN micro-LED display | H. X. Jiang et al., “III-nitride blue microdisplays,” *Applied Physics Letters* 78, 1303–1305 (2001), [doi:10.1063/1.1351521](https://doi.org/10.1063/1.1351521). |

## SiC power devices

| Example concept | Reference |
|---|---|
| SiC rectifiers and vertical switches | J. A. Cooper and A. Agarwal, “SiC power-switching devices—the second electronics revolution?” *Proceedings of the IEEE* 90, 956–968 (2002), [doi:10.1109/JPROC.2002.1021561](https://doi.org/10.1109/JPROC.2002.1021561). |
| Double-implanted SiC MOSFET channel | V. R. Vathulya and M. H. White, “Characterization of inversion and accumulation layer electron transport in 4H and 6H-SiC MOSFETs on implanted P-type regions,” *IEEE Transactions on Electron Devices* 47, 2018–2023 (2000), [doi:10.1109/16.877161](https://doi.org/10.1109/16.877161). |
| Shielded 4H-SiC trench MOSFET | X. Zhou et al., “4H-SiC Trench MOSFET With Floating/Grounded Junction Barrier-controlled Gate Structure,” *IEEE Transactions on Electron Devices* 64, 4568–4574 (2017), [doi:10.1109/TED.2017.2755721](https://doi.org/10.1109/TED.2017.2755721). |
| Vertical 4H-SiC tri-gate MOSFET | R. P. Ramamurthy et al., “The Tri-Gate MOSFET: A New Vertical Power Transistor in 4H-SiC,” *IEEE Electron Device Letters* 42, 90–93 (2021), [doi:10.1109/LED.2020.3040239](https://doi.org/10.1109/LED.2020.3040239). |
