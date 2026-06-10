import requests

msg = r"""# 🧮 Batería Completa de Fórmulas Matemáticas

## Aritmética y Álgebra

**Potencias y raíces:**
$$a^n \cdot a^m = a^{n+m} \qquad \frac{a^n}{a^m} = a^{n-m} \qquad (a^n)^m = a^{nm}$$

$$\sqrt{a} = a^{1/2} \qquad \sqrt[n]{a} = a^{1/n} \qquad \sqrt[3]{x^2 + y^2}$$

**Identidades notables:**
$$(a+b)^2 = a^2 + 2ab + b^2$$
$$(a-b)^2 = a^2 - 2ab + b^2$$
$$(a+b)(a-b) = a^2 - b^2$$

**Fórmula cuadrática:**
$$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$

---

## Sumatorios y Productorios

$$\sum_{i=1}^{n} i = \frac{n(n+1)}{2} \qquad \sum_{i=1}^{n} i^2 = \frac{n(n+1)(2n+1)}{6}$$

$$\prod_{i=1}^{n} i = n! \qquad \binom{n}{k} = \frac{n!}{k!(n-k)!}$$

---

## Límites

$$\lim_{x \to 0} \frac{\sin x}{x} = 1 \qquad \lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x = e$$

$$\lim_{n \to \infty} \sqrt[n]{n} = 1 \qquad \lim_{x \to 0^+} x \ln x = 0$$

---

## Derivadas

**Reglas básicas:**
$$\frac{d}{dx}[x^n] = nx^{n-1} \qquad \frac{d}{dx}[e^x] = e^x \qquad \frac{d}{dx}[\ln x] = \frac{1}{x}$$

**Trigonométricas:**
$$\frac{d}{dx}[\sin x] = \cos x \qquad \frac{d}{dx}[\cos x] = -\sin x \qquad \frac{d}{dx}[\tan x] = \sec^2 x$$

**Regla de la cadena:**
$$\frac{d}{dx}[f(g(x))] = f'(g(x)) \cdot g'(x)$$

**Derivadas parciales:**
$$\nabla f = \frac{\partial f}{\partial x}\hat{i} + \frac{\partial f}{\partial y}\hat{j} + \frac{\partial f}{\partial z}\hat{k}$$

---

## Integrales

**Indefinidas:**
$$\int x^n\,dx = \frac{x^{n+1}}{n+1} + C \qquad \int e^x\,dx = e^x + C \qquad \int \frac{1}{x}\,dx = \ln|x| + C$$

**Definidas:**
$$\int_0^{\pi} \sin x\,dx = 2 \qquad \int_0^1 x^2\,dx = \frac{1}{3}$$

**Integral gaussiana:**
$$\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}$$

**Integración por partes:**
$$\int u\,dv = uv - \int v\,du$$

---

## Matrices y Determinantes

**Matriz 2×2:**
$$A = \begin{pmatrix} a & b \\ c & d \end{pmatrix} \qquad \det(A) = ad - bc$$

**Matriz 3×3:**
$$B = \begin{pmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9 \end{pmatrix}$$

**Determinante 3×3:**
$$\det(B) = \begin{vmatrix} 1 & 2 & 3 \\ 4 & 5 & 6 \\ 7 & 8 & 9 \end{vmatrix} = 0$$

**Inversa:**
$$A^{-1} = \frac{1}{\det(A)} \begin{pmatrix} d & -b \\ -c & a \end{pmatrix}$$

---

## Sistemas de Ecuaciones

$$\begin{cases} 2x + 3y - z = 1 \\ x - y + 2z = 5 \\ 3x + y + z = 8 \end{cases}$$

**Forma matricial:** $A\vec{x} = \vec{b}$

$$\begin{pmatrix} 2 & 3 & -1 \\ 1 & -1 & 2 \\ 3 & 1 & 1 \end{pmatrix} \begin{pmatrix} x \\ y \\ z \end{pmatrix} = \begin{pmatrix} 1 \\ 5 \\ 8 \end{pmatrix}$$

---

## Símbolos Especiales

| Símbolo | LaTeX | Significado |
|---------|-------|-------------|
| $\forall$ | forall | Para todo |
| $\exists$ | exists | Existe |
| $\nexists$ | nexists | No existe |
| $\in$ | in | Pertenece a |
| $\notin$ | notin | No pertenece |
| $\subset$ | subset | Subconjunto |
| $\cup$ | cup | Unión |
| $\cap$ | cap | Intersección |
| $\emptyset$ | emptyset | Vacío |
| $\infty$ | infty | Infinito |
| $\nabla$ | nabla | Nabla |
| $\partial$ | partial | Derivada parcial |
| $\aleph$ | aleph | Aleph |
| $\hbar$ | hbar | h barra |

---

## Ecuaciones Famosas de la Física

**Ecuación de Euler:**
$$e^{i\pi} + 1 = 0$$

**Ecuación de Schrödinger:**
$$i\hbar\frac{\partial}{\partial t}\Psi = \hat{H}\Psi$$

**Ecuaciones de Maxwell:**
$$\nabla \cdot \vec{E} = \frac{\rho}{\varepsilon_0} \qquad \nabla \times \vec{B} = \mu_0\vec{J} + \mu_0\varepsilon_0\frac{\partial \vec{E}}{\partial t}$$

**Relatividad general de Einstein:**
$$R_{\mu\nu} - \frac{1}{2}Rg_{\mu\nu} + \Lambda g_{\mu\nu} = \frac{8\pi G}{c^4}T_{\mu\nu}$$
"""

r = requests.post('http://localhost:7860/api/web_send', json={'message': msg})
print(f"Status: {r.status_code}")
