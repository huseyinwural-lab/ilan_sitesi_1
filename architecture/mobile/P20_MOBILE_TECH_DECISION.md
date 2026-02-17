# P20: Mobile Technology Decision Record

## 1. Executive Summary
**Decision**: We will build the mobile application using **Flutter**.
**Goal**: Create a high-performance, cross-platform (iOS & Android) mobile application that shares a single codebase while offering a near-native user experience.

## 2. Technology Selection Analysis

### 2.1. Framework Choice: Flutter vs. React Native
| Feature | Flutter | React Native | Decision Rationale |
| :--- | :--- | :--- | :--- |
| **Language** | Dart | JavaScript/TypeScript | Dart provides strong typing and AOT compilation, reducing runtime errors. |
| **Performance** | Native (Skia Engine) | Bridge (JS to Native) | Flutter's Skia engine draws every pixel, avoiding the "bridge" bottleneck of RN. |
| **UI Consistency** | Pixel-perfect on all devices | Relies on native components | Critical for our custom UI design language to look identical on iOS/Android. |
| **Dev Speed** | High (Hot Reload) | High (Fast Refresh) | Comparable, but Flutter's widget library speeds up styling. |

**Verdict**: **Flutter** is chosen for its superior performance, UI consistency, and robust ecosystem for "offline-first" architectures.

### 2.2. Core Libraries (Standard Stack)
*   **State Management**: **Riverpod** (Modern, compile-safe, testable).
*   **Navigation**: **go_router** (Deep linking support is critical for our Affiliate system).
*   **Networking**: **Dio** (Better interceptor support for Auth refresh flows than generic http).
*   **Local Storage**: **Hive** (NoSQL, extremely fast for offline caching) + **FlutterSecureStorage** (for tokens).
*   **Service Locator**: **get_it** (Dependency Injection).

## 3. Architecture Pattern
We will use **Clean Architecture** with Feature-first directory structure:
```
lib/
├── src/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   ├── domain/
│   │   │   └── presentation/
│   │   ├── listing/
│   │   └── ...
│   ├── core/
│   │   ├── api/
│   │   └── theme/
│   └── main.dart
```

## 4. Risks & Mitigations
*   **Risk**: Talent pool for Dart is smaller than JS.
    *   *Mitigation*: The syntax is very similar to TS/Java, ensuring low learning curve for existing team.
*   **Risk**: App size is larger.
    *   *Mitigation*: Use `appbundle` and `ipa` optimization to strip unused code.

## 5. Conclusion
Proceed with **Flutter** setup. The project will reside in a separate repository (or `mobile/` folder if monorepo) but communicate exclusively via the documented API.
