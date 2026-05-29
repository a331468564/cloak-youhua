<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 设计规格变更时更新
read_when:  需要了解优化设计决策时读取
delete_when: 不删除
-->
# Ron Group Lead Research MVP - Optimization Design

> Status: Brainstorming Complete
> Date: 2026-05-18
> Next: /write-plan

---

## 1. Current State Analysis

### 1.1 Project Overview

- **Purpose**: B2B lead research for Ron Group, Australia restaurant/hotel focus
- **Data**: 195 leads, 128 contacts, 80 Australia leads
- **Tools**: Scrapling, Playwright, Python scripts, Dashboard

### 1.2 Strengths

- Clear business goal and market focus
- Structured CSV data with 53 fields
- Multiple extraction scripts (static, dynamic, stealth)
- Comprehensive documentation (13 docs)
- Local dashboard for manual review

### 1.3 Weaknesses Identified

| Area | Issue | Impact |
|------|-------|--------|
| **Structure** | Reports scattered, no clear phase separation | Hard to navigate |
| **Docs** | 107KB request-solution-log, duplicated info | Token waste |
| **Code** | Scripts lack unified interface | Inconsistent usage |
| **Workflow** | No clear state machine | Unclear progress |

---

## 2. Optimization Proposals

### 2.1 Project Structure Reorganization

**Current:**
```
TestProject/
├── data/
├── dashboard/
├── docs/
├── scripts/
├── reports/
└── skills/
```

**Proposed:**
```
TestProject-v2/
├── data/                    # Raw data (unchanged)
│   ├── leads.csv
│   ├── contacts.csv
│   └── ...
├── dashboard/               # Dashboard (unchanged)
├── docs/                    # Documentation
│   ├── architecture/        # NEW: Architecture docs
│   ├── workflows/           # NEW: Workflow docs
│   ├── guides/              # NEW: User guides
│   └── logs/                # NEW: Change logs
├── scripts/                 # Scripts
│   ├── extraction/          # NEW: Extraction scripts
│   ├── analysis/            # NEW: Analysis scripts
│   └── utils/               # NEW: Utility scripts
├── reports/                 # Reports
│   ├── australia/           # NEW: Australia reports
│   ├── experiments/         # NEW: Experiment results
│   └── batches/             # NEW: Batch reports
├── tests/                   # NEW: Test scripts
└── config/                  # NEW: Configuration files
```

### 2.2 Documentation Optimization

**Problem:** `request-solution-log.md` is 107KB, contains too much history.

**Solution:**
1. Archive old entries (>30 days) to `docs/logs/archive/`
2. Keep only active entries in main log
3. Create index file for quick lookup
4. Standardize entry format

**Documentation Hierarchy:**
```
docs/
├── README.md                # Quick start
├── architecture/
│   ├── system-overview.md   # System architecture
│   └── data-model.md        # Data schema
├── workflows/
│   ├── lead-collection.md   # Collection workflow
│   ├── lead-enrichment.md   # Enrichment workflow
│   └── dashboard-usage.md   # Dashboard guide
├── guides/
│   ├── setup.md             # Environment setup
│   └── troubleshooting.md   # Common issues
└── logs/
    ├── changelog.md         # Recent changes
    └── archive/             # Old logs
```

### 2.3 Code Quality Improvement

**Current Issues:**
- Scripts have inconsistent interfaces
- No unified error handling
- No logging framework
- No test coverage

**Proposed Improvements:**

1. **Unified Script Interface**
```python
# scripts/base.py
class BaseScript:
    def __init__(self, config):
        self.config = config
        self.logger = self.setup_logger()

    def run(self):
        raise NotImplementedError

    def setup_logger(self):
        # Unified logging
        pass
```

2. **Configuration Management**
```python
# config/settings.py
class ProjectConfig:
    DATA_DIR = "data"
    REPORTS_DIR = "reports"
    # ...
```

3. **Error Handling**
```python
# scripts/utils/errors.py
class ProjectError(Exception):
    pass

class DataError(ProjectError):
    pass

class ExtractionError(ProjectError):
    pass
```

### 2.4 Workflow Optimization

**Current Workflow:**
```
Search → Extract → Review → Update CSV → Report
```

**Proposed State Machine:**
```
[Discovery] → [Extraction] → [Validation] → [Registration] → [Enrichment] → [Ready]
     ↓              ↓              ↓              ↓              ↓
  Keywords      Candidates     Review         CSV Update     KP Search
```

**State Tracking:**
```python
# scripts/workflow/state.py
class LeadState:
    DISCOVERY = "discovery"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    REGISTRATION = "registration"
    ENRICHMENT = "enrichment"
    READY = "ready"
```

---

## 3. Implementation Plan

### Phase 1: Structure Reorganization (Priority: High)

- [ ] Create new directory structure
- [ ] Move files to appropriate locations
- [ ] Update all file references
- [ ] Verify no broken links

### Phase 2: Documentation Cleanup (Priority: High)

- [ ] Archive old request-solution-log entries
- [ ] Create documentation index
- [ ] Standardize entry format
- [ ] Remove duplicate content

### Phase 3: Code Refactoring (Priority: Medium)

- [ ] Create base script class
- [ ] Implement configuration management
- [ ] Add unified error handling
- [ ] Add logging framework

### Phase 4: Workflow Implementation (Priority: Medium)

- [ ] Define state machine
- [ ] Create state tracking
- [ ] Implement transitions
- [ ] Add validation rules

### Phase 5: Testing (Priority: Low)

- [ ] Create test framework
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add workflow tests

---

## 4. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| File reference breakage | High | Medium | Systematic search-replace |
| Data loss during move | Low | High | Backup before changes |
| Workflow disruption | Medium | High | Keep old structure as fallback |
| Time overrun | Medium | Medium | Prioritize Phase 1-2 |

---

## 5. Success Criteria

- [ ] All files accessible from new locations
- [ ] Documentation reduced by 50%
- [ ] Scripts have unified interface
- [ ] Workflow states clearly defined
- [ ] No broken references
- [ ] All existing functionality preserved

---

## 6. Questions for User

1. **Directory naming**: Use `extraction/` or `collectors/` for extraction scripts?
2. **Archive threshold**: Archive logs older than 30 days or 60 days?
3. **Test priority**: Should we add tests now or focus on structure first?
4. **Dashboard changes**: Keep dashboard as-is or integrate with new structure?

---

## Next Steps

After user approval:
1. Run `/write-plan` to create detailed implementation plan
2. Execute plan with Superpowers TDD methodology
3. Verify all changes with systematic debugging
4. Document results in request-solution-log
